"""Contrato do registro create-only sem vazamento de segredos."""

import hashlib
import hmac

import httpx
import pytest
from pydantic import SecretStr

from social_internal_backend.synapse import (
    SynapseRegistrationClient,
    SynapseRegistrationConflictError,
    SynapseRegistrationProtocolError,
    SynapseRegistrationUnavailableError,
    compute_registration_mac,
)


def test_registration_mac_uses_synapse_field_order() -> None:
    expected = hmac.new(
        b"secret",
        b"nonce\x00employee\x00opaque-password\x00notadmin",
        hashlib.sha1,
    ).hexdigest()
    assert compute_registration_mac("secret", "nonce", "employee", "opaque-password") == expected


def test_register_returns_masked_ephemeral_session() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "GET":
            return httpx.Response(200, json={"nonce": "nonce"})
        return httpx.Response(
            200,
            json={
                "user_id": "@employee:localhost",
                "device_id": "DEVICE",
                "access_token": "opaque-access-token",
            },
        )

    with SynapseRegistrationClient(
        base_url="http://synapse",
        timeout_seconds=5,
        shared_secret=SecretStr("shared-secret"),
        transport=httpx.MockTransport(handler),
    ) as client:
        session = client.register(
            username="employee",
            password=SecretStr("valid-password-value"),
        )

    assert session.user_id == "@employee:localhost"
    assert session.device_id == "DEVICE"
    assert session.access_token.get_secret_value() == "opaque-access-token"
    assert "opaque-access-token" not in repr(session)
    assert len(requests) == 2
    assert b'"admin":false' in requests[1].content
    assert b"shared-secret" not in requests[1].content


@pytest.mark.parametrize("status_code", [400, 409])
def test_existing_identity_is_a_create_only_conflict(status_code: int) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, json={"nonce": "nonce"})
        return httpx.Response(status_code, json={"errcode": "M_USER_IN_USE"})

    client = SynapseRegistrationClient(
        base_url="http://synapse",
        timeout_seconds=5,
        shared_secret=SecretStr("shared-secret"),
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(SynapseRegistrationConflictError):
        client.register(username="employee", password=SecretStr("valid-password-value"))
    client.close()


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, json={}),
        httpx.Response(200, json=[]),
        httpx.Response(200, content=b"not-json"),
    ],
)
def test_invalid_nonce_response_is_protocol_error(response: httpx.Response) -> None:
    client = SynapseRegistrationClient(
        base_url="http://synapse",
        timeout_seconds=5,
        shared_secret=SecretStr("shared-secret"),
        transport=httpx.MockTransport(lambda request: response),
    )
    with pytest.raises(SynapseRegistrationProtocolError):
        client.register(username="employee", password=SecretStr("valid-password-value"))
    client.close()


def test_post_network_failure_is_marked_ambiguous() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, json={"nonce": "nonce"})
        raise httpx.ConnectError("unavailable", request=request)

    client = SynapseRegistrationClient(
        base_url="http://synapse",
        timeout_seconds=5,
        shared_secret=SecretStr("shared-secret"),
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(SynapseRegistrationUnavailableError) as captured:
        client.register(username="employee", password=SecretStr("valid-password-value"))
    assert captured.value.ambiguous is True
    client.close()


def test_password_and_shared_secret_are_validated() -> None:
    with pytest.raises(ValueError):
        SynapseRegistrationClient(
            base_url="http://synapse",
            timeout_seconds=5,
            shared_secret=SecretStr(""),
        )
    client = SynapseRegistrationClient(
        base_url="http://synapse",
        timeout_seconds=5,
        shared_secret=SecretStr("shared-secret"),
        transport=httpx.MockTransport(lambda request: httpx.Response(500)),
    )
    with pytest.raises(ValueError):
        client.register(username="employee", password=SecretStr("short"))
    client.close()
