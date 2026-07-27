"""Contrato HTTP público e sanitizado da pré-validação."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from pydantic import SecretStr

from social_internal_backend.activations import (
    ActivationValidationConflictError,
    ActivationValidationNotFoundError,
    ActivationValidationRateLimitedError,
    ActivationValidationResult,
    ActivationValidationStorageUnavailableError,
    ActivationValidationUnavailableError,
)
from social_internal_backend.api.activation_validations import ActivationValidationRequest
from social_internal_backend.api.dependencies import get_activation_validation_service
from social_internal_backend.application import create_app
from social_internal_backend.models import InvitationRole
from social_internal_backend.settings import Settings
from social_internal_backend.synapse import (
    InvalidSynapseAdminCredentialError,
    SynapseAdminProtocolError,
    SynapseAdminRateLimitedError,
    SynapseAdminUnavailableError,
)

NOW = datetime(2026, 7, 27, 12, tzinfo=UTC)
OPAQUE_INVITATION_VALUE = "opaque-activation-value"


class FakeActivationValidationService:
    def __init__(self) -> None:
        self.error: Exception | None = None
        self.received_token: str | None = None

    def validate(self, invitation_token: str) -> ActivationValidationResult:
        self.received_token = invitation_token
        if self.error is not None:
            raise self.error
        return ActivationValidationResult(
            target_user_id="@employee:localhost",
            username="employee",
            role=InvitationRole.user,
            expires_at=NOW + timedelta(hours=12),
        )


def test_request_representation_masks_invitation_token() -> None:
    payload = ActivationValidationRequest(invitation_token=OPAQUE_INVITATION_VALUE)

    assert OPAQUE_INVITATION_VALUE not in repr(payload)
    assert OPAQUE_INVITATION_VALUE not in str(payload.model_dump())


@asynccontextmanager
async def make_client(
    settings: Settings,
    service: FakeActivationValidationService,
) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(settings)

    def override_service() -> FakeActivationValidationService:
        return service

    app.dependency_overrides[get_activation_validation_service] = override_service
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.anyio
async def test_valid_token_returns_read_only_identity_without_authentication(
    settings: Settings,
) -> None:
    service = FakeActivationValidationService()
    async with make_client(settings, service) as client:
        response = await client.post(
            "/v1/activation-validations",
            json={"invitation_token": OPAQUE_INVITATION_VALUE},
        )

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {
        "target_user_id": "@employee:localhost",
        "username": "employee",
        "role": "user",
        "expires_at": "2026-07-28T00:00:00Z",
    }
    assert service.received_token == OPAQUE_INVITATION_VALUE
    assert OPAQUE_INVITATION_VALUE not in response.text
    assert "authorization" not in response.request.headers


@pytest.mark.anyio
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"invitation_token": ""},
        {"invitation_token": "x" * 513},
        {"invitation_token": OPAQUE_INVITATION_VALUE, "username": "attacker"},
        {"invitation_token": OPAQUE_INVITATION_VALUE, "role": "platform_admin"},
    ],
)
async def test_invalid_body_returns_sanitized_422(
    settings: Settings,
    payload: dict[str, object],
) -> None:
    service = FakeActivationValidationService()
    async with make_client(settings, service) as client:
        response = await client.post("/v1/activation-validations", json=payload)

    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {"error": {"code": "invalid_request"}}
    assert OPAQUE_INVITATION_VALUE not in response.text
    assert "attacker" not in response.text
    assert service.received_token is None


@pytest.mark.anyio
async def test_query_parameters_are_rejected_without_processing(
    settings: Settings,
) -> None:
    service = FakeActivationValidationService()
    async with make_client(settings, service) as client:
        response = await client.post(
            f"/v1/activation-validations?invitation_token={OPAQUE_INVITATION_VALUE}",
            json={"invitation_token": OPAQUE_INVITATION_VALUE},
        )

    assert response.status_code == 422
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {"error": {"code": "invalid_request"}}
    assert OPAQUE_INVITATION_VALUE not in response.text
    assert service.received_token is None


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("error", "expected_status", "expected_code"),
    [
        (ActivationValidationNotFoundError(), 404, "activation_not_found"),
        (ActivationValidationUnavailableError(), 410, "activation_unavailable"),
        (ActivationValidationConflictError(), 409, "activation_conflict"),
        (
            ActivationValidationStorageUnavailableError(),
            503,
            "service_unavailable",
        ),
        (SynapseAdminRateLimitedError(), 503, "service_unavailable"),
        (SynapseAdminProtocolError(), 502, "upstream_invalid_response"),
        (InvalidSynapseAdminCredentialError(), 503, "service_unavailable"),
        (SynapseAdminUnavailableError(), 503, "service_unavailable"),
    ],
)
async def test_known_failures_use_stable_envelope_without_secret(
    settings: Settings,
    error: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    service = FakeActivationValidationService()
    service.error = error
    async with make_client(settings, service) as client:
        response = await client.post(
            "/v1/activation-validations",
            json={"invitation_token": OPAQUE_INVITATION_VALUE},
        )

    assert response.status_code == expected_status
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {"error": {"code": expected_code}}
    assert OPAQUE_INVITATION_VALUE not in response.text


@pytest.mark.anyio
async def test_rate_limit_includes_retry_after_without_internal_count(
    settings: Settings,
) -> None:
    service = FakeActivationValidationService()
    service.error = ActivationValidationRateLimitedError(37)
    async with make_client(settings, service) as client:
        response = await client.post(
            "/v1/activation-validations",
            json={"invitation_token": OPAQUE_INVITATION_VALUE},
        )

    assert response.status_code == 429
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["retry-after"] == "37"
    assert response.json() == {"error": {"code": "rate_limited"}}
    assert "10" not in response.text


@pytest.mark.anyio
async def test_unexpected_failure_is_sanitized_with_no_store(settings: Settings) -> None:
    service = FakeActivationValidationService()
    service.error = RuntimeError(OPAQUE_INVITATION_VALUE)
    async with make_client(settings, service) as client:
        response = await client.post(
            "/v1/activation-validations",
            json={"invitation_token": OPAQUE_INVITATION_VALUE},
        )

    assert response.status_code == 500
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {"error": {"code": "service_unavailable"}}
    assert OPAQUE_INVITATION_VALUE not in response.text


@pytest.mark.anyio
async def test_method_not_allowed_still_uses_no_store(settings: Settings) -> None:
    service = FakeActivationValidationService()
    async with make_client(settings, service) as client:
        response = await client.get("/v1/activation-validations")

    assert response.status_code == 405
    assert response.headers["cache-control"] == "no-store"
    assert service.received_token is None


@pytest.mark.anyio
async def test_trailing_slash_redirect_uses_no_store(settings: Settings) -> None:
    service = FakeActivationValidationService()
    async with make_client(settings, service) as client:
        response = await client.post(
            "/v1/activation-validations/",
            json={"invitation_token": OPAQUE_INVITATION_VALUE},
            follow_redirects=False,
        )

    assert response.status_code == 307
    assert response.headers["cache-control"] == "no-store"
    assert OPAQUE_INVITATION_VALUE not in response.headers["location"]
    assert service.received_token is None


@pytest.mark.anyio
async def test_invalid_backend_credential_fails_as_sanitized_503(
    settings: Settings,
) -> None:
    invalid_settings = settings.model_copy(
        update={"synapse_admin_access_token": SecretStr("invalid credential")}
    )
    app = create_app(invalid_settings)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/v1/activation-validations",
            json={"invitation_token": OPAQUE_INVITATION_VALUE},
        )

    assert response.status_code == 503
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {"error": {"code": "service_unavailable"}}
    assert "invalid credential" not in response.text
