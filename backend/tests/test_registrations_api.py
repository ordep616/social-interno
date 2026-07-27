"""Contrato público sanitizado da criação de contas."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest
from pydantic import SecretStr

from social_internal_backend.api.dependencies import get_registration_service
from social_internal_backend.api.registrations import RegistrationRequest
from social_internal_backend.application import create_app
from social_internal_backend.registrations import (
    RegistrationConflictError,
    RegistrationNotFoundError,
    RegistrationPasswordPolicyError,
    RegistrationRateLimitedError,
    RegistrationResult,
    RegistrationStorageUnavailableError,
    RegistrationUnavailableError,
    RegistrationUpstreamInvalidResponseError,
    RegistrationUpstreamUnavailableError,
)
from social_internal_backend.settings import Settings

OPAQUE_INVITATION_VALUE = "opaque-invitation-value"
OPAQUE_PASSWORD_VALUE = "opaque-password-value"  # noqa: S105


class FakeRegistrationService:
    error: Exception | None = None

    def register(self, invitation_token: str, password: SecretStr) -> RegistrationResult:
        assert invitation_token == OPAQUE_INVITATION_VALUE
        assert password.get_secret_value() == OPAQUE_PASSWORD_VALUE
        if self.error is not None:
            raise self.error
        return RegistrationResult(user_id="@employee:localhost")


@asynccontextmanager
async def make_client(
    settings: Settings, service: FakeRegistrationService
) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(settings)
    app.dependency_overrides[get_registration_service] = lambda: service
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


def test_request_masks_both_secrets() -> None:
    payload = RegistrationRequest(
        invitation_token=OPAQUE_INVITATION_VALUE,
        password=OPAQUE_PASSWORD_VALUE,
    )
    assert OPAQUE_INVITATION_VALUE not in repr(payload)
    assert OPAQUE_PASSWORD_VALUE not in repr(payload)


@pytest.mark.anyio
async def test_success_returns_only_created_identity(settings: Settings) -> None:
    async with make_client(settings, FakeRegistrationService()) as client:
        response = await client.post(
            "/v1/registrations",
            json={
                "invitation_token": OPAQUE_INVITATION_VALUE,
                "password": OPAQUE_PASSWORD_VALUE,
            },
        )
    assert response.status_code == 201
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {"user_id": "@employee:localhost"}
    assert OPAQUE_INVITATION_VALUE not in response.text
    assert OPAQUE_PASSWORD_VALUE not in response.text


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("error", "status_code", "code"),
    [
        (RegistrationNotFoundError(), 404, "activation_not_found"),
        (RegistrationUnavailableError(), 410, "activation_unavailable"),
        (RegistrationConflictError(), 409, "activation_conflict"),
        (RegistrationPasswordPolicyError(), 422, "password_policy_violation"),
        (RegistrationStorageUnavailableError(), 503, "service_unavailable"),
        (RegistrationUpstreamUnavailableError(), 503, "service_unavailable"),
        (RegistrationUpstreamInvalidResponseError(), 502, "upstream_invalid_response"),
    ],
)
async def test_known_errors_are_sanitized(
    settings: Settings,
    error: Exception,
    status_code: int,
    code: str,
) -> None:
    service = FakeRegistrationService()
    service.error = error
    async with make_client(settings, service) as client:
        response = await client.post(
            "/v1/registrations",
            json={
                "invitation_token": OPAQUE_INVITATION_VALUE,
                "password": OPAQUE_PASSWORD_VALUE,
            },
        )
    assert response.status_code == status_code
    assert response.json() == {"error": {"code": code}}
    assert OPAQUE_INVITATION_VALUE not in response.text
    assert OPAQUE_PASSWORD_VALUE not in response.text


@pytest.mark.anyio
async def test_rate_limit_returns_retry_after(settings: Settings) -> None:
    service = FakeRegistrationService()
    service.error = RegistrationRateLimitedError(42)
    async with make_client(settings, service) as client:
        response = await client.post(
            "/v1/registrations",
            json={
                "invitation_token": OPAQUE_INVITATION_VALUE,
                "password": OPAQUE_PASSWORD_VALUE,
            },
        )
    assert response.status_code == 429
    assert response.headers["retry-after"] == "42"
    assert response.json() == {"error": {"code": "rate_limited"}}


@pytest.mark.anyio
async def test_invalid_body_and_query_do_not_echo_secrets(settings: Settings) -> None:
    service = FakeRegistrationService()
    async with make_client(settings, service) as client:
        invalid = await client.post(
            "/v1/registrations",
            json={
                "invitation_token": OPAQUE_INVITATION_VALUE,
                "password": "short",
                "role": "platform_admin",
            },
        )
        query = await client.post(
            f"/v1/registrations?token={OPAQUE_INVITATION_VALUE}",
            json={
                "invitation_token": OPAQUE_INVITATION_VALUE,
                "password": OPAQUE_PASSWORD_VALUE,
            },
        )
    assert invalid.json() == {"error": {"code": "invalid_request"}}
    assert query.json() == {"error": {"code": "invalid_request"}}
    assert OPAQUE_INVITATION_VALUE not in invalid.text
    assert OPAQUE_INVITATION_VALUE not in query.text
