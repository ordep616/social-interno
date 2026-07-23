"""Cliente isolado da API administrativa de usuários do Synapse."""

import json
from collections.abc import Callable

import httpx
import pytest
from pydantic import SecretStr

from social_internal_backend.synapse import (
    InvalidSynapseAdminCredentialError,
    SynapseAdminClient,
    SynapseAdminProtocolError,
    SynapseAdminRateLimitedError,
    SynapseAdminUnavailableError,
    SynapseUserAlreadyExistsError,
    SynapseUserNotFoundError,
)

BASE_URL = "http://synapse.test"
SERVER_NAME = "localhost"
OPAQUE_ADMIN_VALUE = "opaque-admin-value-for-tests"
OPAQUE_ACCOUNT_VALUE = "opaque-account-value-for-tests"
USER_ID = "@alice:localhost"


def make_user_payload(user_id: str = USER_ID) -> dict[str, object]:
    """Produz somente os campos que o cliente decidiu interpretar."""

    return {
        "name": user_id,
        "admin": False,
        "deactivated": False,
        "locked": False,
        "suspended": False,
    }


def make_client(
    handler: Callable[[httpx.Request], httpx.Response],
    *,
    server_name: str = SERVER_NAME,
    admin_value: str = OPAQUE_ADMIN_VALUE,
) -> SynapseAdminClient:
    return SynapseAdminClient(
        base_url=BASE_URL,
        timeout_seconds=1,
        matrix_server_name=server_name,
        admin_access_token=SecretStr(admin_value),
        transport=httpx.MockTransport(handler),
    )


@pytest.mark.parametrize("timeout_seconds", [0, -1, 31])
def test_admin_client_rejects_unsafe_timeout(timeout_seconds: float) -> None:
    with pytest.raises(ValueError, match="timeout_seconds"):
        SynapseAdminClient(
            base_url=BASE_URL,
            timeout_seconds=timeout_seconds,
            matrix_server_name=SERVER_NAME,
            admin_access_token=SecretStr(OPAQUE_ADMIN_VALUE),
        )


@pytest.mark.parametrize(
    "server_name",
    ["", "https://localhost", "local/host", "local host", "x" * 256],
)
def test_admin_client_rejects_invalid_server_name(server_name: str) -> None:
    with pytest.raises(ValueError, match="server name"):
        SynapseAdminClient(
            base_url=BASE_URL,
            timeout_seconds=1,
            matrix_server_name=server_name,
            admin_access_token=SecretStr(OPAQUE_ADMIN_VALUE),
        )


@pytest.mark.parametrize(
    "admin_value",
    ["", "contains space", "line\nbreak", "x" * 4097],
)
def test_admin_client_rejects_unsafe_credential(admin_value: str) -> None:
    with pytest.raises(InvalidSynapseAdminCredentialError):
        SynapseAdminClient(
            base_url=BASE_URL,
            timeout_seconds=1,
            matrix_server_name=SERVER_NAME,
            admin_access_token=SecretStr(admin_value),
        )


def test_get_user_uses_encoded_path_bearer_header_and_minimal_result() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.raw_path == (b"/_synapse/admin/v2/users/%40alice%3Alocalhost")
        assert request.url.query == b""
        assert request.headers["Authorization"] == f"Bearer {OPAQUE_ADMIN_VALUE}"
        assert request.content == b""
        return httpx.Response(200, json=make_user_payload())

    with make_client(handler) as client:
        user = client.get_user(USER_ID)

    assert user.user_id == USER_ID
    assert not user.admin
    assert not user.deactivated
    assert not user.locked
    assert not user.suspended
    assert OPAQUE_ADMIN_VALUE not in repr(user)


def test_get_user_maps_missing_account_without_response_details() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(404, json={"error": OPAQUE_ADMIN_VALUE})

    with (
        make_client(handler) as client,
        pytest.raises(SynapseUserNotFoundError) as captured,
    ):
        client.get_user(USER_ID)

    assert OPAQUE_ADMIN_VALUE not in str(captured.value)


def test_create_user_preflights_and_sends_only_non_admin_account_fields() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.headers["Authorization"] == f"Bearer {OPAQUE_ADMIN_VALUE}"
        if request.method == "GET":
            return httpx.Response(404)
        assert request.method == "PUT"
        assert request.url.raw_path == (b"/_synapse/admin/v2/users/%40alice%3Alocalhost")
        assert json.loads(request.content) == {
            "password": OPAQUE_ACCOUNT_VALUE,
            "admin": False,
            "deactivated": False,
            "locked": False,
        }
        return httpx.Response(201, json={"name": USER_ID})

    with make_client(handler) as client:
        created = client.create_user(
            user_id=USER_ID,
            password=SecretStr(OPAQUE_ACCOUNT_VALUE),
        )

    assert [request.method for request in requests] == ["GET", "PUT"]
    assert created.user_id == USER_ID
    assert OPAQUE_ACCOUNT_VALUE not in repr(created)
    assert OPAQUE_ADMIN_VALUE not in repr(created)


def test_create_user_stops_before_put_when_account_exists() -> None:
    requests = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        assert request.method == "GET"
        return httpx.Response(200, json=make_user_payload())

    with (
        make_client(handler) as client,
        pytest.raises(SynapseUserAlreadyExistsError),
    ):
        client.create_user(
            user_id=USER_ID,
            password=SecretStr(OPAQUE_ACCOUNT_VALUE),
        )

    assert requests == 1


@pytest.mark.parametrize("status_code", [200, 409])
def test_create_user_treats_non_created_account_as_conflict(
    status_code: int,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(404)
        return httpx.Response(status_code, json={"error": OPAQUE_ACCOUNT_VALUE})

    with (
        make_client(handler) as client,
        pytest.raises(SynapseUserAlreadyExistsError) as captured,
    ):
        client.create_user(
            user_id=USER_ID,
            password=SecretStr(OPAQUE_ACCOUNT_VALUE),
        )

    assert OPAQUE_ACCOUNT_VALUE not in str(captured.value)


@pytest.mark.parametrize(
    ("status_code", "expected_error"),
    [
        (401, InvalidSynapseAdminCredentialError),
        (403, InvalidSynapseAdminCredentialError),
        (429, SynapseAdminRateLimitedError),
        (500, SynapseAdminUnavailableError),
        (503, SynapseAdminUnavailableError),
        (418, SynapseAdminProtocolError),
    ],
)
def test_get_user_classifies_sanitized_failures(
    status_code: int,
    expected_error: type[Exception],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(status_code, json={"error": OPAQUE_ADMIN_VALUE})

    with (
        make_client(handler) as client,
        pytest.raises(expected_error) as captured,
    ):
        client.get_user(USER_ID)

    assert OPAQUE_ADMIN_VALUE not in str(captured.value)


@pytest.mark.parametrize(
    ("status_code", "expected_error"),
    [
        (401, InvalidSynapseAdminCredentialError),
        (429, SynapseAdminRateLimitedError),
        (500, SynapseAdminUnavailableError),
        (418, SynapseAdminProtocolError),
    ],
)
def test_create_user_classifies_sanitized_put_failures(
    status_code: int,
    expected_error: type[Exception],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(404)
        return httpx.Response(status_code, json={"error": OPAQUE_ACCOUNT_VALUE})

    with (
        make_client(handler) as client,
        pytest.raises(expected_error) as captured,
    ):
        client.create_user(
            user_id=USER_ID,
            password=SecretStr(OPAQUE_ACCOUNT_VALUE),
        )

    assert OPAQUE_ACCOUNT_VALUE not in str(captured.value)
    assert OPAQUE_ADMIN_VALUE not in str(captured.value)


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {},
        {"name": 123},
        {
            **make_user_payload(),
            "admin": 0,
        },
        {
            **make_user_payload(),
            "deactivated": "false",
        },
        {
            **make_user_payload(),
            "locked": None,
        },
        {
            **make_user_payload(),
            "suspended": 0,
        },
        make_user_payload("@other:localhost"),
        make_user_payload("@alice:other"),
    ],
)
def test_get_user_rejects_malformed_or_mismatched_payload(payload: object) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(200, json=payload)

    with make_client(handler) as client, pytest.raises(SynapseAdminProtocolError):
        client.get_user(USER_ID)


def test_get_user_rejects_invalid_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(200, content=b"not-json")

    with make_client(handler) as client, pytest.raises(SynapseAdminProtocolError):
        client.get_user(USER_ID)


@pytest.mark.parametrize(
    ("user_id", "password_value"),
    [
        ("invalid", OPAQUE_ACCOUNT_VALUE),
        ("@alice:other", OPAQUE_ACCOUNT_VALUE),
        (USER_ID, ""),
        (USER_ID, "x" * 513),
    ],
)
def test_create_user_rejects_invalid_input_before_request(
    user_id: str,
    password_value: str,
) -> None:
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        del request
        return httpx.Response(201)

    with make_client(handler) as client, pytest.raises(ValueError):
        client.create_user(
            user_id=user_id,
            password=SecretStr(password_value),
        )
    assert not called


def test_admin_client_sanitizes_network_failure_and_exception_chain() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(
            f"failed with {OPAQUE_ADMIN_VALUE}",
            request=request,
        )

    with (
        make_client(handler) as client,
        pytest.raises(SynapseAdminUnavailableError) as captured,
    ):
        client.get_user(USER_ID)

    assert captured.value.__cause__ is None
    assert OPAQUE_ADMIN_VALUE not in str(captured.value)


def test_admin_client_does_not_follow_redirect_with_credential() -> None:
    requests = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        return httpx.Response(
            302,
            headers={"Location": "https://other.example/admin"},
        )

    with make_client(handler) as client, pytest.raises(SynapseAdminProtocolError):
        client.get_user(USER_ID)
    assert requests == 1


def test_admin_client_repr_does_not_expose_credential() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        del request
        return httpx.Response(404)

    with make_client(handler) as client:
        representation = repr(client)

    assert OPAQUE_ADMIN_VALUE not in representation
