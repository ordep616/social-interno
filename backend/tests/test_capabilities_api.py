"""Contrato HTTP das capacidades corporativas da identidade atual."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import httpx
import pytest

from social_internal_backend.api.dependencies import get_user_capabilities_service
from social_internal_backend.application import create_app
from social_internal_backend.authorization import (
    CorporateUserAccessDeniedError,
    UserCapabilitiesContext,
)
from social_internal_backend.models import UserRole, UserRoleAssignment
from social_internal_backend.settings import Settings
from social_internal_backend.synapse import (
    InvalidMatrixAccessTokenError,
    MatrixIdentity,
    SynapseProtocolError,
    SynapseRateLimitedError,
    SynapseUnavailableError,
)

OPAQUE_MATRIX_VALUE = "opaque-matrix-value"
USER_ID = "@employee:localhost"
AUTHORIZATION_HEADER = {"Authorization": f"Bearer {OPAQUE_MATRIX_VALUE}"}


def make_capabilities(role: UserRole) -> UserCapabilitiesContext:
    return UserCapabilitiesContext(
        identity=MatrixIdentity(
            user_id=USER_ID,
            is_guest=False,
            device_id="DEVICE",
        ),
        assignment=UserRoleAssignment(
            matrix_user_id=USER_ID,
            role=role,
            granted_at=datetime(2026, 7, 23, 10, tzinfo=UTC),
            granted_by="@admin:localhost",
        ),
    )


class FakeUserCapabilitiesService:
    """Controla a borda HTTP sem chamar Synapse ou PostgreSQL."""

    def __init__(self, role: UserRole = UserRole.user) -> None:
        self.context = make_capabilities(role)
        self.error: Exception | None = None
        self.received_token: str | None = None

    def resolve(self, access_token: str) -> UserCapabilitiesContext:
        self.received_token = access_token
        if self.error is not None:
            raise self.error
        return self.context


@asynccontextmanager
async def make_client(
    settings: Settings,
    capabilities: FakeUserCapabilitiesService,
) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(settings)

    def override_capabilities_service() -> FakeUserCapabilitiesService:
        return capabilities

    app.dependency_overrides[get_user_capabilities_service] = override_capabilities_service
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("role", "expected_capability"),
    [
        (UserRole.user, False),
        (UserRole.group_admin, False),
        (UserRole.platform_admin, True),
    ],
)
async def test_returns_role_and_backend_calculated_capability(
    settings: Settings,
    role: UserRole,
    expected_capability: bool,
) -> None:
    capabilities = FakeUserCapabilitiesService(role)
    async with make_client(settings, capabilities) as client:
        response = await client.get(
            "/v1/me/capabilities",
            headers=AUTHORIZATION_HEADER,
        )

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {
        "user_id": USER_ID,
        "role": role.value,
        "capabilities": {
            "can_manage_user_activations": expected_capability,
        },
    }
    assert capabilities.received_token == OPAQUE_MATRIX_VALUE
    assert OPAQUE_MATRIX_VALUE not in response.text


@pytest.mark.anyio
async def test_missing_matrix_authentication_is_denied_without_service_call(
    settings: Settings,
) -> None:
    capabilities = FakeUserCapabilitiesService()
    async with make_client(settings, capabilities) as client:
        response = await client.get("/v1/me/capabilities")

    assert response.status_code == 401
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["www-authenticate"] == "Bearer"
    assert capabilities.received_token is None


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (InvalidMatrixAccessTokenError(), 401),
        (CorporateUserAccessDeniedError(), 403),
        (SynapseRateLimitedError(), 503),
        (SynapseUnavailableError(), 503),
        (SynapseProtocolError(), 502),
    ],
)
async def test_maps_authentication_failures_without_exposing_credentials(
    settings: Settings,
    error: Exception,
    expected_status: int,
) -> None:
    capabilities = FakeUserCapabilitiesService()
    capabilities.error = error
    async with make_client(settings, capabilities) as client:
        response = await client.get(
            "/v1/me/capabilities",
            headers=AUTHORIZATION_HEADER,
        )

    assert response.status_code == expected_status
    assert response.headers["cache-control"] == "no-store"
    assert OPAQUE_MATRIX_VALUE not in response.text
    if expected_status == 401:
        assert response.headers["www-authenticate"] == "Bearer"
