"""Contrato HTTP dos endpoints administrativos de convites."""

from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi import HTTPException
from pydantic import SecretStr
from sqlalchemy.orm import Session

from social_internal_backend.api import dependencies as api_dependencies
from social_internal_backend.api.dependencies import (
    get_invitation_issuance_service,
    get_invitation_service,
    get_platform_admin_authorization_service,
)
from social_internal_backend.application import create_app
from social_internal_backend.authorization import (
    AuthorizedPlatformAdmin,
    PlatformAdminAccessDeniedError,
)
from social_internal_backend.invitations import (
    InvitationConflictError,
    InvitationIdentityConflictError,
    InvitationNotFoundError,
    IssuedInvitation,
)
from social_internal_backend.models import (
    Invitation,
    InvitationRole,
    InvitationStatus,
    UserRole,
    UserRoleAssignment,
)
from social_internal_backend.settings import Settings
from social_internal_backend.synapse import (
    InvalidMatrixAccessTokenError,
    InvalidSynapseAdminCredentialError,
    MatrixIdentity,
    SynapseAdminProtocolError,
    SynapseAdminRateLimitedError,
    SynapseAdminUnavailableError,
    SynapseProtocolError,
    SynapseRateLimitedError,
    SynapseUnavailableError,
    SynapseUserNotFoundError,
)

NOW = datetime(2026, 7, 23, 15, tzinfo=UTC)
OPAQUE_INVITATION_VALUE = "opaque-invitation-value"
OPAQUE_MATRIX_VALUE = "opaque-matrix-value"
ADMIN_USER_ID = "@admin:localhost"
AUTHORIZATION_HEADER = {"Authorization": f"Bearer {OPAQUE_MATRIX_VALUE}"}


def make_invitation(
    *,
    role: InvitationRole = InvitationRole.user,
    status: InvitationStatus = InvitationStatus.pending,
) -> Invitation:
    """Cria um modelo completo sem depender do PostgreSQL."""

    return Invitation(
        id=uuid4(),
        token_hash="a" * 64,
        role=role,
        status=status,
        created_by=ADMIN_USER_ID,
        target_user_id="@employee:localhost",
        created_at=NOW,
        expires_at=NOW + timedelta(hours=24),
        used_at=None,
        revoked_at=None,
        accepted_user_id=None,
    )


def make_authorized_admin() -> AuthorizedPlatformAdmin:
    """Cria o contexto seguro produzido depois do `whoami`."""

    assignment = UserRoleAssignment(
        matrix_user_id=ADMIN_USER_ID,
        role=UserRole.platform_admin,
        granted_at=NOW,
        granted_by=None,
    )
    return AuthorizedPlatformAdmin(
        identity=MatrixIdentity(
            user_id=ADMIN_USER_ID,
            is_guest=False,
            device_id="DEVICE",
        ),
        assignment=assignment,
    )


class FakeAuthorizationService:
    """Controla autorização sem chamar o Synapse ou conservar a credencial."""

    def __init__(self) -> None:
        self.error: Exception | None = None
        self.received_token: str | None = None

    def authorize(self, access_token: str) -> AuthorizedPlatformAdmin:
        self.received_token = access_token
        if self.error is not None:
            raise self.error
        return make_authorized_admin()


class FakeInvitationService:
    """Controla resultados das regras já testadas em outra unidade."""

    def __init__(self) -> None:
        self.invitation = make_invitation()
        self.listed: Sequence[Invitation] = [self.invitation]
        self.get_error: Exception | None = None
        self.revoke_error: Exception | None = None
        self.issue_error: Exception | None = None
        self.omit_issued_target = False
        self.issue_arguments: tuple[str, InvitationRole, str] | None = None
        self.list_arguments: tuple[int, int] | None = None
        self.requested_id: UUID | None = None
        self.revoked_id: UUID | None = None

    def issue(
        self,
        *,
        role: InvitationRole,
        created_by: str,
        username: str | None = None,
    ) -> IssuedInvitation:
        if username is None:
            raise AssertionError("username must be provided by the endpoint")
        self.issue_arguments = (username, role, created_by)
        if self.issue_error is not None:
            raise self.issue_error
        self.invitation.role = role
        self.invitation.target_user_id = (
            None if self.omit_issued_target else f"@{username}:localhost"
        )
        return IssuedInvitation(invitation=self.invitation, token=OPAQUE_INVITATION_VALUE)

    def list(self, *, offset: int = 0, limit: int = 100) -> Sequence[Invitation]:
        self.list_arguments = (offset, limit)
        return self.listed

    def get(self, invitation_id: UUID) -> Invitation:
        self.requested_id = invitation_id
        if self.get_error is not None:
            raise self.get_error
        return self.invitation

    def revoke(self, invitation_id: UUID) -> Invitation:
        self.revoked_id = invitation_id
        if self.revoke_error is not None:
            raise self.revoke_error
        return self.invitation


@asynccontextmanager
async def make_client(
    settings: Settings,
    invitations: FakeInvitationService,
    authorization: FakeAuthorizationService,
) -> AsyncIterator[httpx.AsyncClient]:
    """Substitui somente as bordas externas das dependências HTTP."""

    app = create_app(settings)

    def override_invitation_service() -> FakeInvitationService:
        return invitations

    def override_authorization_service() -> FakeAuthorizationService:
        return authorization

    app.dependency_overrides[get_invitation_service] = override_invitation_service
    app.dependency_overrides[get_invitation_issuance_service] = override_invitation_service
    app.dependency_overrides[get_platform_admin_authorization_service] = (
        override_authorization_service
    )
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.anyio
async def test_create_returns_location_single_secret_and_no_store(settings: Settings) -> None:
    invitations = FakeInvitationService()
    authorization = FakeAuthorizationService()
    async with make_client(settings, invitations, authorization) as client:
        response = await client.post(
            "/v1/admin/invitations",
            headers=AUTHORIZATION_HEADER,
            json={"username": "employee", "role": "group_admin"},
        )

    assert response.status_code == 201
    assert response.headers["location"] == (f"/v1/admin/invitations/{invitations.invitation.id}")
    assert response.headers["cache-control"] == "no-store"
    assert invitations.issue_arguments == (
        "employee",
        InvitationRole.group_admin,
        ADMIN_USER_ID,
    )
    assert authorization.received_token == OPAQUE_MATRIX_VALUE
    payload = response.json()
    assert payload["role"] == "group_admin"
    assert payload["status"] == "pending"
    assert payload["target_user_id"] == "@employee:localhost"
    assert payload["invite_url"] == (f"http://127.0.0.1:8080/activate#{OPAQUE_INVITATION_VALUE}")
    assert OPAQUE_INVITATION_VALUE not in payload["invite_url"].split("#", maxsplit=1)[0]
    assert "token_hash" not in payload
    assert OPAQUE_INVITATION_VALUE not in repr(invitations.invitation)


@pytest.mark.anyio
async def test_list_and_get_use_public_identifiers_without_hash(settings: Settings) -> None:
    invitations = FakeInvitationService()
    authorization = FakeAuthorizationService()
    async with make_client(settings, invitations, authorization) as client:
        listed = await client.get(
            "/v1/admin/invitations?offset=3&limit=25",
            headers=AUTHORIZATION_HEADER,
        )
        fetched = await client.get(
            f"/v1/admin/invitations/{invitations.invitation.id}",
            headers=AUTHORIZATION_HEADER,
        )

    assert listed.status_code == 200
    assert listed.headers["cache-control"] == "no-store"
    assert invitations.list_arguments == (3, 25)
    assert len(listed.json()) == 1
    assert "target_user_id" not in listed.json()[0]
    assert "token_hash" not in listed.json()[0]
    assert fetched.status_code == 200
    assert fetched.headers["cache-control"] == "no-store"
    assert invitations.requested_id == invitations.invitation.id
    assert fetched.json()["id"] == str(invitations.invitation.id)
    assert "target_user_id" not in fetched.json()
    assert "invite_url" not in fetched.json()


@pytest.mark.anyio
async def test_revoke_returns_idempotent_empty_response(settings: Settings) -> None:
    invitations = FakeInvitationService()
    authorization = FakeAuthorizationService()
    async with make_client(settings, invitations, authorization) as client:
        first = await client.delete(
            f"/v1/admin/invitations/{invitations.invitation.id}",
            headers=AUTHORIZATION_HEADER,
        )
        second = await client.delete(
            f"/v1/admin/invitations/{invitations.invitation.id}",
            headers=AUTHORIZATION_HEADER,
        )

    assert first.status_code == 204
    assert first.content == b""
    assert first.headers["cache-control"] == "no-store"
    assert second.status_code == 204
    assert invitations.revoked_id == invitations.invitation.id


@pytest.mark.anyio
@pytest.mark.parametrize("header", [None, {"Authorization": "Basic value"}])
async def test_admin_routes_require_bearer_authentication(
    settings: Settings,
    header: dict[str, str] | None,
) -> None:
    invitations = FakeInvitationService()
    authorization = FakeAuthorizationService()
    async with make_client(settings, invitations, authorization) as client:
        response = await client.get(
            "/v1/admin/invitations",
            headers=header,
        )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.headers["cache-control"] == "no-store"
    assert authorization.received_token is None


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (InvalidMatrixAccessTokenError(), 401),
        (PlatformAdminAccessDeniedError(), 403),
        (SynapseRateLimitedError(), 503),
        (SynapseUnavailableError(), 503),
        (SynapseProtocolError(), 502),
    ],
)
async def test_admin_routes_map_authorization_failures_without_secret(
    settings: Settings,
    error: Exception,
    expected_status: int,
) -> None:
    invitations = FakeInvitationService()
    authorization = FakeAuthorizationService()
    authorization.error = error
    async with make_client(settings, invitations, authorization) as client:
        response = await client.get(
            "/v1/admin/invitations",
            headers=AUTHORIZATION_HEADER,
        )

    assert response.status_code == expected_status
    assert response.headers["cache-control"] == "no-store"
    assert OPAQUE_MATRIX_VALUE not in response.text


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("operation", "error", "expected_status"),
    [
        ("get", InvitationNotFoundError(), 404),
        ("revoke", InvitationNotFoundError(), 404),
        ("revoke", InvitationConflictError(), 409),
    ],
)
async def test_resource_failures_follow_rest_contract(
    settings: Settings,
    operation: str,
    error: Exception,
    expected_status: int,
) -> None:
    invitations = FakeInvitationService()
    authorization = FakeAuthorizationService()
    if operation == "get":
        invitations.get_error = error
    else:
        invitations.revoke_error = error

    async with make_client(settings, invitations, authorization) as client:
        response = await client.request(
            "GET" if operation == "get" else "DELETE",
            f"/v1/admin/invitations/{invitations.invitation.id}",
            headers=AUTHORIZATION_HEADER,
        )

    assert response.status_code == expected_status
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.anyio
async def test_request_validation_rejects_forbidden_role_and_bad_pagination(
    settings: Settings,
) -> None:
    invitations = FakeInvitationService()
    authorization = FakeAuthorizationService()
    async with make_client(settings, invitations, authorization) as client:
        role_response = await client.post(
            "/v1/admin/invitations",
            headers=AUTHORIZATION_HEADER,
            json={"username": "employee", "role": "platform_admin"},
        )
        username_response = await client.post(
            "/v1/admin/invitations",
            headers=AUTHORIZATION_HEADER,
            json={"username": "Employee", "role": "user"},
        )
        pagination_response = await client.get(
            "/v1/admin/invitations?limit=101",
            headers=AUTHORIZATION_HEADER,
        )
        uuid_response = await client.get(
            "/v1/admin/invitations/not-a-uuid",
            headers=AUTHORIZATION_HEADER,
        )

    for response in (role_response, username_response, pagination_response, uuid_response):
        assert response.status_code == 422
        assert response.headers["cache-control"] == "no-store"
    assert invitations.issue_arguments is None


@pytest.mark.anyio
@pytest.mark.parametrize(
    "extra_field",
    [
        {"target_user_id": "@attacker:localhost"},
        {"created_by": "@attacker:localhost"},
        {"platform_admin": True},
    ],
)
async def test_create_rejects_unapproved_request_fields(
    settings: Settings,
    extra_field: dict[str, object],
) -> None:
    invitations = FakeInvitationService()
    authorization = FakeAuthorizationService()
    async with make_client(settings, invitations, authorization) as client:
        response = await client.post(
            "/v1/admin/invitations",
            headers=AUTHORIZATION_HEADER,
            json={
                "username": "employee",
                "role": "user",
                **extra_field,
            },
        )

    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"
    assert invitations.issue_arguments is None


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (InvitationIdentityConflictError(), 409),
        (SynapseAdminRateLimitedError(), 429),
        (InvalidSynapseAdminCredentialError(), 503),
        (SynapseAdminUnavailableError(), 503),
        (SynapseAdminProtocolError(), 502),
    ],
)
async def test_create_maps_identity_availability_failures_without_secret(
    settings: Settings,
    error: Exception,
    expected_status: int,
) -> None:
    invitations = FakeInvitationService()
    invitations.issue_error = error
    authorization = FakeAuthorizationService()
    async with make_client(settings, invitations, authorization) as client:
        response = await client.post(
            "/v1/admin/invitations",
            headers=AUTHORIZATION_HEADER,
            json={"username": "employee", "role": "user"},
        )

    assert response.status_code == expected_status
    assert response.headers["cache-control"] == "no-store"
    assert OPAQUE_INVITATION_VALUE not in response.text
    assert OPAQUE_MATRIX_VALUE not in response.text


@pytest.mark.anyio
async def test_create_rejects_internal_result_without_target_identity(
    settings: Settings,
) -> None:
    invitations = FakeInvitationService()
    invitations.omit_issued_target = True
    authorization = FakeAuthorizationService()
    async with make_client(settings, invitations, authorization) as client:
        response = await client.post(
            "/v1/admin/invitations",
            headers=AUTHORIZATION_HEADER,
            json={"username": "employee", "role": "user"},
        )

    assert response.status_code == 500
    assert response.headers["cache-control"] == "no-store"
    assert OPAQUE_INVITATION_VALUE not in response.text


def test_issuance_dependency_rejects_invalid_admin_credential(settings: Settings) -> None:
    invalid_settings = settings.model_copy(
        update={"synapse_admin_access_token": SecretStr("")},
    )
    dependency = get_invitation_issuance_service(
        invalid_settings,
        MagicMock(spec=Session),
    )

    with pytest.raises(HTTPException) as captured:
        next(dependency)

    assert captured.value.status_code == 503
    assert captured.value.headers == {"Cache-Control": "no-store"}


def test_issuance_dependency_wires_and_closes_admin_client(
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSynapseAdminClient:
        """Confirma a composição sem abrir conexão HTTP."""

        def __init__(
            self,
            *,
            base_url: str,
            timeout_seconds: float,
            matrix_server_name: str,
            admin_access_token: SecretStr,
        ) -> None:
            assert base_url == str(settings.synapse_base_url)
            assert timeout_seconds == settings.synapse_request_timeout_seconds
            assert matrix_server_name == settings.matrix_server_name
            assert admin_access_token is settings.synapse_admin_access_token
            self.requested_user_id: str | None = None
            self.closed = False
            clients.append(self)

        def __enter__(self) -> FakeSynapseAdminClient:
            return self

        def __exit__(self, *args: object) -> None:
            del args
            self.closed = True

        def get_user(self, user_id: str) -> object:
            self.requested_user_id = user_id
            raise SynapseUserNotFoundError

    clients: list[FakeSynapseAdminClient] = []
    monkeypatch.setattr(
        api_dependencies,
        "SynapseAdminClient",
        FakeSynapseAdminClient,
    )
    session = MagicMock(spec=Session)
    session.scalars.return_value.one_or_none.return_value = None
    dependency = api_dependencies.get_invitation_issuance_service(settings, session)

    service = next(dependency)
    issued = service.issue(
        role=InvitationRole.user,
        created_by=ADMIN_USER_ID,
        username="employee",
    )
    with pytest.raises(StopIteration):
        next(dependency)

    assert issued.invitation.target_user_id == "@employee:localhost"
    assert clients[0].requested_user_id == "@employee:localhost"
    assert clients[0].closed


@pytest.mark.anyio
async def test_openapi_documents_all_admin_invitation_operations(settings: Settings) -> None:
    invitations = FakeInvitationService()
    authorization = FakeAuthorizationService()
    async with make_client(settings, invitations, authorization) as client:
        response = await client.get("/openapi.json")

    paths = response.json()["paths"]
    assert {"get", "post"} <= paths["/v1/admin/invitations"].keys()
    assert {"get", "delete"} <= paths["/v1/admin/invitations/{invitation_id}"].keys()
