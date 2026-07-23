"""Validação de identidade pelo endpoint Matrix `whoami`."""

from collections.abc import Callable

import httpx
import pytest

from social_internal_backend.synapse import (
    InvalidMatrixAccessTokenError,
    SynapseClient,
    SynapseProtocolError,
    SynapseRateLimitedError,
    SynapseUnavailableError,
)

BASE_URL = "http://synapse.test"
OPAQUE_VALUE = "opaque-value-for-tests"


def make_client(handler: Callable[[httpx.Request], httpx.Response]) -> SynapseClient:
    return SynapseClient(
        base_url=BASE_URL,
        timeout_seconds=1,
        transport=httpx.MockTransport(handler),
    )


@pytest.mark.parametrize("timeout_seconds", [0, -1, 31])
def test_client_rejects_unsafe_timeout(timeout_seconds: float) -> None:
    with pytest.raises(ValueError, match="timeout_seconds"):
        SynapseClient(base_url=BASE_URL, timeout_seconds=timeout_seconds)


def test_whoami_uses_bearer_header_without_query_or_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/_matrix/client/v3/account/whoami"
        assert request.url.query == b""
        assert request.headers["Authorization"] == f"Bearer {OPAQUE_VALUE}"
        assert request.content == b""
        return httpx.Response(
            200,
            json={
                "user_id": "@admin:localhost",
                "device_id": "DEVICE",
                "is_guest": False,
            },
        )

    with make_client(handler) as client:
        identity = client.whoami(OPAQUE_VALUE)

    assert identity.user_id == "@admin:localhost"
    assert identity.device_id == "DEVICE"
    assert not identity.is_guest
    assert OPAQUE_VALUE not in repr(identity)


def test_whoami_accepts_optional_fields_and_guest_flag() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(200, json={"user_id": "@guest:localhost", "is_guest": True})

    with make_client(handler) as client:
        identity = client.whoami(OPAQUE_VALUE)

    assert identity.is_guest
    assert identity.device_id is None


@pytest.mark.parametrize("status_code", [401, 403])
def test_whoami_maps_rejected_credentials_to_sanitized_error(status_code: int) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(status_code, json={"error": OPAQUE_VALUE})

    with (
        make_client(handler) as client,
        pytest.raises(InvalidMatrixAccessTokenError) as captured,
    ):
        client.whoami(OPAQUE_VALUE)

    assert OPAQUE_VALUE not in str(captured.value)


@pytest.mark.parametrize(
    ("status_code", "expected_error"),
    [
        (429, SynapseRateLimitedError),
        (500, SynapseUnavailableError),
        (503, SynapseUnavailableError),
        (418, SynapseProtocolError),
    ],
)
def test_whoami_classifies_non_success_responses(
    status_code: int,
    expected_error: type[Exception],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(status_code)

    with make_client(handler) as client, pytest.raises(expected_error):
        client.whoami(OPAQUE_VALUE)


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {},
        {"user_id": 123},
        {"user_id": "invalid"},
        {"user_id": "@admin:localhost", "is_guest": "false"},
        {"user_id": "@admin:localhost", "device_id": 123},
    ],
)
def test_whoami_rejects_malformed_success_payload(payload: object) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(200, json=payload)

    with make_client(handler) as client, pytest.raises(SynapseProtocolError):
        client.whoami(OPAQUE_VALUE)


def test_whoami_rejects_invalid_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(200, content=b"not-json")

    with make_client(handler) as client, pytest.raises(SynapseProtocolError):
        client.whoami(OPAQUE_VALUE)


@pytest.mark.parametrize("invalid_value", ["", "contains space", "line\nbreak", "x" * 4097])
def test_whoami_rejects_unsafe_token_before_request(invalid_value: str) -> None:
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        del request
        return httpx.Response(200)

    with make_client(handler) as client, pytest.raises(InvalidMatrixAccessTokenError):
        client.whoami(invalid_value)
    assert not called


def test_whoami_sanitizes_network_failure_and_exception_chain() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(f"failed with {OPAQUE_VALUE}", request=request)

    with make_client(handler) as client, pytest.raises(SynapseUnavailableError) as captured:
        client.whoami(OPAQUE_VALUE)

    assert captured.value.__cause__ is None
    assert OPAQUE_VALUE not in str(captured.value)


def test_whoami_does_not_follow_redirect_with_authorization_header() -> None:
    requests = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        return httpx.Response(302, headers={"Location": "https://other.example/whoami"})

    with make_client(handler) as client, pytest.raises(SynapseProtocolError):
        client.whoami(OPAQUE_VALUE)
    assert requests == 1
