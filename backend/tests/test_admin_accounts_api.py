"""Contrato HTTP dos endpoints administrativos de contas."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import httpx
import pytest
from pydantic import SecretStr

from social_internal_backend.api.dependencies import (
    get_account_service,
    get_audit_service,
    get_platform_admin_authorization_service,
)
from social_internal_backend.application import create_app
from social_internal_backend.authorization import (
    AuthorizedPlatformAdmin,
    PlatformAdminAccessDeniedError,
)
from social_internal_backend.models import UserRole, UserRoleAssignment
from social_internal_backend.settings import Settings
from social_internal_backend.synapse import (
    InvalidMatrixAccessTokenError,
    MatrixIdentity,
    SynapseAdminProtocolError,
    SynapseAdminUnavailableError,
    SynapseProtocolError,
    SynapseRateLimitedError,
    SynapseUnavailableError,
    SynapseUser,
    SynapseUserNotFoundError,
    SynapseUserPage,
)

NOW = datetime(2026, 7, 24, 14, tzinfo=UTC)
OPAQUE_MATRIX_VALUE = "opaque-matrix-value"
OPAQUE_PASSWORD_VALUE = "opaque-password-value"  # noqa: S105
ADMIN_USER_ID = "@admin:localhost"
EMPLOYEE_USER_ID = "@employee:localhost"
AUTHORIZATION_HEADER = {"Authorization": f"Bearer {OPAQUE_MATRIX_VALUE}"}


def make_authorized_admin() -> AuthorizedPlatformAdmin:
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


def make_synapse_user(
    *,
    user_id: str = EMPLOYEE_USER_ID,
    display_name: str | None = "Funcionario",
    admin: bool = False,
    deactivated: bool = False,
    locked: bool = False,
    suspended: bool = False,
) -> SynapseUser:
    return SynapseUser(
        user_id=user_id,
        display_name=display_name,
        admin=admin,
        deactivated=deactivated,
        locked=locked,
        suspended=suspended,
    )


class FakeAuthorizationService:
    def __init__(self) -> None:
        self.error: Exception | None = None
        self.received_token: str | None = None

    def authorize(self, access_token: str) -> AuthorizedPlatformAdmin:
        self.received_token = access_token
        if self.error is not None:
            raise self.error
        return make_authorized_admin()


class FakeAccountService:
    def __init__(self) -> None:
        self.page = SynapseUserPage(
            users=(make_synapse_user(),),
            total=1,
            next_token=None,
        )
        self.error: Exception | None = None
        self.list_arguments: tuple[int, int, str | None] | None = None
        self.update_arguments: tuple[str, str | None, bool | None] | None = None
        self.reset_arguments: tuple[str, SecretStr, bool] | None = None
        self.deactivate_arguments: tuple[str, bool] | None = None

    def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        query: str | None = None,
    ) -> SynapseUserPage:
        self.list_arguments = (offset, limit, query)
        if self.error is not None:
            raise self.error
        return self.page

    def update(
        self,
        *,
        user_id: str,
        display_name: str | None = None,
        locked: bool | None = None,
    ) -> SynapseUser:
        self.update_arguments = (user_id, display_name, locked)
        if self.error is not None:
            raise self.error
        return make_synapse_user(display_name=display_name, locked=locked is True)

    def reset_password(
        self,
        *,
        user_id: str,
        new_password: SecretStr,
        logout_devices: bool = True,
    ) -> None:
        self.reset_arguments = (user_id, new_password, logout_devices)
        if self.error is not None:
            raise self.error

    def deactivate(self, *, user_id: str, erase: bool) -> None:
        self.deactivate_arguments = (user_id, erase)
        if self.error is not None:
            raise self.error


class FakeAuditService:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def record(self, **event: object) -> object:
        self.events.append(event)
        return object()


@asynccontextmanager
async def make_client(
    settings: Settings,
    accounts: FakeAccountService,
    authorization: FakeAuthorizationService,
) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(settings)

    def override_account_service() -> FakeAccountService:
        return accounts

    def override_authorization_service() -> FakeAuthorizationService:
        return authorization

    app.dependency_overrides[get_account_service] = override_account_service
    app.dependency_overrides[get_audit_service] = lambda: FakeAuditService()
    app.dependency_overrides[get_platform_admin_authorization_service] = (
        override_authorization_service
    )
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.anyio
async def test_list_accounts_returns_no_store_page(settings: Settings) -> None:
    accounts = FakeAccountService()
    authorization = FakeAuthorizationService()
    async with make_client(settings, accounts, authorization) as client:
        response = await client.get(
            "/v1/admin/accounts?offset=2&limit=25&query=emp",
            headers=AUTHORIZATION_HEADER,
        )

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert accounts.list_arguments == (2, 25, "emp")
    assert authorization.received_token == OPAQUE_MATRIX_VALUE
    assert response.json() == {
        "accounts": [
            {
                "user_id": EMPLOYEE_USER_ID,
                "display_name": "Funcionario",
                "role": None,
                "admin": False,
                "deactivated": False,
                "locked": False,
                "suspended": False,
            }
        ],
        "total": 1,
        "next_token": None,
    }


@pytest.mark.anyio
async def test_update_reset_and_deactivate_call_service(settings: Settings) -> None:
    accounts = FakeAccountService()
    authorization = FakeAuthorizationService()
    path_user_id = "%40employee%3Alocalhost"

    async with make_client(settings, accounts, authorization) as client:
        updated = await client.patch(
            f"/v1/admin/accounts/{path_user_id}",
            headers=AUTHORIZATION_HEADER,
            json={"display_name": "Funcionario Atualizado", "locked": True},
        )
        reset = await client.post(
            f"/v1/admin/accounts/{path_user_id}/password-reset",
            headers=AUTHORIZATION_HEADER,
            json={"new_password": OPAQUE_PASSWORD_VALUE, "logout_devices": True},
        )
        deactivated = await client.delete(
            f"/v1/admin/accounts/{path_user_id}?erase=true",
            headers=AUTHORIZATION_HEADER,
        )

    assert updated.status_code == 200
    assert updated.headers["cache-control"] == "no-store"
    assert updated.json()["display_name"] == "Funcionario Atualizado"
    assert updated.json()["locked"] is True
    assert accounts.update_arguments == (
        EMPLOYEE_USER_ID,
        "Funcionario Atualizado",
        True,
    )
    assert reset.status_code == 204
    assert reset.headers["cache-control"] == "no-store"
    assert accounts.reset_arguments is not None
    assert accounts.reset_arguments[0] == EMPLOYEE_USER_ID
    assert accounts.reset_arguments[1].get_secret_value() == OPAQUE_PASSWORD_VALUE
    assert OPAQUE_PASSWORD_VALUE not in response_text_or_empty(reset)
    assert deactivated.status_code == 204
    assert accounts.deactivate_arguments == (EMPLOYEE_USER_ID, True)


@pytest.mark.anyio
@pytest.mark.parametrize("header", [None, {"Authorization": "Basic value"}])
async def test_account_routes_require_bearer_authentication(
    settings: Settings,
    header: dict[str, str] | None,
) -> None:
    accounts = FakeAccountService()
    authorization = FakeAuthorizationService()
    async with make_client(settings, accounts, authorization) as client:
        response = await client.get("/v1/admin/accounts", headers=header)

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
async def test_account_routes_map_authorization_failures(
    settings: Settings,
    error: Exception,
    expected_status: int,
) -> None:
    accounts = FakeAccountService()
    authorization = FakeAuthorizationService()
    authorization.error = error
    async with make_client(settings, accounts, authorization) as client:
        response = await client.get("/v1/admin/accounts", headers=AUTHORIZATION_HEADER)

    assert response.status_code == expected_status
    assert response.headers["cache-control"] == "no-store"
    assert OPAQUE_MATRIX_VALUE not in response.text


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (SynapseUserNotFoundError(), 404),
        (SynapseAdminUnavailableError(), 503),
        (SynapseAdminProtocolError(), 502),
        (ValueError("invalid"), 422),
    ],
)
async def test_account_routes_map_service_failures(
    settings: Settings,
    error: Exception,
    expected_status: int,
) -> None:
    accounts = FakeAccountService()
    accounts.error = error
    authorization = FakeAuthorizationService()
    async with make_client(settings, accounts, authorization) as client:
        response = await client.get("/v1/admin/accounts", headers=AUTHORIZATION_HEADER)

    assert response.status_code == expected_status
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.anyio
async def test_openapi_documents_account_operations(settings: Settings) -> None:
    accounts = FakeAccountService()
    authorization = FakeAuthorizationService()
    async with make_client(settings, accounts, authorization) as client:
        response = await client.get("/openapi.json")

    paths = response.json()["paths"]
    assert {"get"} <= paths["/v1/admin/accounts"].keys()
    assert {"patch", "delete"} <= paths["/v1/admin/accounts/{user_id}"].keys()
    assert {"post"} <= paths["/v1/admin/accounts/{user_id}/password-reset"].keys()


def response_text_or_empty(response: httpx.Response) -> str:
    return response.text if response.content else ""
