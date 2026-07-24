#!/usr/bin/env python3
"""Executa uma POC create-only contra uma stack Synapse descartável."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import (
    HTTPRedirectHandler,
    ProxyHandler,
    Request,
    build_opener,
)

POC_DIR = Path(__file__).resolve().parent
COMPOSE_FILE = POC_DIR / "compose.yaml"
LOG_CONFIG_FILE = POC_DIR / "synapse-log.config"
SYNAPSE_IMAGE = "ghcr.io/element-hq/synapse:v1.156.0"
EXPECTED_SYNAPSE_VERSION = "1.156.0"
SERVER_NAME = "poc.localhost"
REGISTRATION_PATH = "/_synapse/admin/v1/register"
WHOAMI_PATH = "/_matrix/client/v3/account/whoami"
LOGIN_PATH = "/_matrix/client/v3/login"
LOGOUT_PATH = "/_matrix/client/v3/logout"
USER_ADMIN_PATH = "/_synapse/admin/v2/users"
SERVER_VERSION_PATH = "/_synapse/admin/v1/server_version"
HTTP_TIMEOUT_SECONDS = 10
STARTUP_TIMEOUT_SECONDS = 180
MAX_RESPONSE_BYTES = 1_000_000


class PocError(RuntimeError):
    """Falha sanitizada da prova de conceito."""


@dataclass(frozen=True, slots=True)
class ApiResponse:
    """Resposta HTTP mínima sem conservar a requisição."""

    status: int
    payload: object


@dataclass(frozen=True, slots=True)
class RegisteredSession:
    """Sessão temporária retornada pelo registro administrativo."""

    user_id: str
    access_token: str
    device_id: str


class NoRedirectHandler(HTTPRedirectHandler):
    """Impede que credenciais sejam encaminhadas por redirecionamento."""

    def redirect_request(
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        del req, fp, code, msg, headers, newurl
        return None


class SafeHttpClient:
    """Cliente local que nunca inclui corpo ou credencial nas exceções."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._opener = build_opener(ProxyHandler({}), NoRedirectHandler())

    def request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        payload: dict[str, object] | None = None,
    ) -> ApiResponse:
        body = None
        headers = {"Accept": "application/json", "Connection": "close"}
        if payload is not None:
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"

        request = Request(
            f"{self._base_url}{path}",
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with self._opener.open(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
                raw_body = response.read(MAX_RESPONSE_BYTES)
                return ApiResponse(response.status, _decode_json(raw_body))
        except HTTPError as error:
            raw_body = error.read(MAX_RESPONSE_BYTES)
            return ApiResponse(error.code, _decode_json(raw_body))
        except (TimeoutError, URLError, OSError):
            raise PocError("local Synapse request failed") from None


def _decode_json(raw_body: bytes) -> object:
    if not raw_body:
        return {}
    try:
        return json.loads(raw_body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def _require_status(response: ApiResponse, expected: int, operation: str) -> None:
    if response.status != expected:
        raise PocError(f"{operation} returned unexpected HTTP status")


def _require_dict(response: ApiResponse, operation: str) -> dict[str, object]:
    if not isinstance(response.payload, dict):
        raise PocError(f"{operation} returned an invalid JSON object")
    return response.payload


def _require_string(payload: dict[str, object], field: str, operation: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value:
        raise PocError(f"{operation} omitted a required field")
    return value


def compute_registration_mac(
    shared_secret: str,
    nonce: str,
    username: str,
    password: str,
    *,
    admin: bool,
) -> str:
    """Calcula o HMAC exigido exclusivamente pela API do Synapse."""

    message = b"\x00".join(
        (
            nonce.encode("utf-8"),
            username.encode("utf-8"),
            password.encode("utf-8"),
            b"admin" if admin else b"notadmin",
        )
    )
    return hmac.new(
        shared_secret.encode("utf-8"),
        message,
        digestmod=hashlib.sha1,
    ).hexdigest()


def exact_identity_matches(
    session: RegisteredSession,
    *,
    expected_user_id: str,
    expected_device_id: str,
) -> bool:
    """Compara identidade, domínio e dispositivo sem normalização."""

    if session.user_id != expected_user_id or session.device_id != expected_device_id:
        return False
    if not session.user_id.startswith("@") or ":" not in session.user_id:
        return False
    _, server_name = session.user_id[1:].split(":", maxsplit=1)
    return server_name == SERVER_NAME


def stable_account_snapshot(payload: dict[str, object]) -> dict[str, object]:
    """Seleciona propriedades que uma tentativa create-only não pode alterar."""

    fields = (
        "name",
        "displayname",
        "avatar_url",
        "is_guest",
        "admin",
        "deactivated",
        "erased",
        "shadow_banned",
        "appservice_id",
        "user_type",
        "locked",
        "suspended",
        "approved",
        "creation_ts",
    )
    return {field: payload.get(field) for field in fields if field in payload}


def sensitive_categories_in_text(
    text: str,
    sensitive_values: dict[str, set[str]],
) -> list[str]:
    """Retorna somente categorias, nunca os valores encontrados."""

    return sorted(
        category
        for category, values in sensitive_values.items()
        if any(len(value) >= 8 and value in text for value in values)
    )


def _record_sensitive(
    sensitive_values: dict[str, set[str]],
    category: str,
    value: str,
) -> None:
    sensitive_values.setdefault(category, set()).add(value)


def _free_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", 0))
        return int(server.getsockname()[1])


def _write_runtime(
    runtime_dir: Path,
    *,
    postgres_password: str,
    registration_secret: str,
    macaroon_secret: str,
    form_secret: str,
) -> Path:
    registration_secret_file = runtime_dir / "registration_shared_secret"
    registration_secret_file.write_text(f"{registration_secret}\n", encoding="utf-8")
    registration_secret_file.chmod(0o600)

    shutil.copyfile(LOG_CONFIG_FILE, runtime_dir / "log.config")
    homeserver_config = f"""server_name: "{SERVER_NAME}"
public_baseurl: "http://127.0.0.1:8008/"
pid_file: /data/homeserver.pid
listeners:
  - port: 8008
    tls: false
    type: http
    x_forwarded: false
    bind_addresses: ["0.0.0.0"]
    resources:
      - names: [client]
        compress: false

database:
  name: psycopg2
  args:
    user: "synapse"
    password: "{postgres_password}"
    dbname: "synapse"
    host: postgres
    port: 5432
    cp_min: 2
    cp_max: 5

media_store_path: /data/media_store
uploads_path: /data/uploads
enable_registration: false
enable_registration_without_verification: false
registration_shared_secret_path: "/run/secrets/registration_shared_secret"
allow_public_rooms_without_auth: false
allow_public_rooms_over_federation: false
federation_domain_whitelist: []
trusted_key_servers: []
suppress_key_server_warning: true
report_stats: false
url_preview_enabled: false
macaroon_secret_key: "{macaroon_secret}"
form_secret: "{form_secret}"
signing_key_path: /data/signing.key
log_config: /data/log.config
"""
    homeserver_path = runtime_dir / "homeserver.yaml"
    homeserver_path.write_text(homeserver_config, encoding="utf-8")
    homeserver_path.chmod(0o600)
    return registration_secret_file


def _compose_command(project_name: str, *arguments: str) -> list[str]:
    return [
        "docker",
        "compose",
        "--project-name",
        project_name,
        "--file",
        str(COMPOSE_FILE),
        *arguments,
    ]


def _run_command(
    command: list[str],
    *,
    environment: dict[str, str],
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            cwd=POC_DIR,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
            timeout=STARTUP_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        if check:
            raise PocError("disposable Docker operation timed out") from None
        return subprocess.CompletedProcess(command, 124, "", "")
    if check and result.returncode != 0:
        raise PocError("disposable Docker operation failed")
    return result


def _wait_for_synapse(client: SafeHttpClient) -> None:
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        try:
            response = client.request("GET", "/_matrix/client/versions")
        except PocError:
            time.sleep(1)
            continue
        if response.status == 200:
            return
        time.sleep(1)
    raise PocError("disposable Synapse did not become healthy")


def _registration_request(
    client: SafeHttpClient,
    *,
    shared_secret: str,
    username: str,
    password: str,
    admin: bool,
    sensitive_values: dict[str, set[str]],
) -> ApiResponse:
    nonce_response = client.request("GET", REGISTRATION_PATH)
    _require_status(nonce_response, 200, "registration nonce")
    nonce_payload = _require_dict(nonce_response, "registration nonce")
    nonce = _require_string(nonce_payload, "nonce", "registration nonce")
    mac = compute_registration_mac(
        shared_secret,
        nonce,
        username,
        password,
        admin=admin,
    )
    _record_sensitive(sensitive_values, "nonce", nonce)
    _record_sensitive(sensitive_values, "mac", mac)
    return client.request(
        "POST",
        REGISTRATION_PATH,
        payload={
            "nonce": nonce,
            "username": username,
            "password": password,
            "admin": admin,
            "mac": mac,
        },
    )


def _parse_registered_session(
    response: ApiResponse,
    *,
    operation: str,
    sensitive_values: dict[str, set[str]],
) -> RegisteredSession:
    _require_status(response, 200, operation)
    payload = _require_dict(response, operation)
    access_token = _require_string(payload, "access_token", operation)
    session = RegisteredSession(
        user_id=_require_string(payload, "user_id", operation),
        access_token=access_token,
        device_id=_require_string(payload, "device_id", operation),
    )
    _record_sensitive(sensitive_values, "access_token", access_token)
    return session


def _whoami(client: SafeHttpClient, token: str) -> ApiResponse:
    return client.request("GET", WHOAMI_PATH, token=token)


def _assert_whoami(
    client: SafeHttpClient,
    session: RegisteredSession,
    *,
    expected_user_id: str,
) -> None:
    response = _whoami(client, session.access_token)
    _require_status(response, 200, "whoami before revocation")
    payload = _require_dict(response, "whoami before revocation")
    confirmed = RegisteredSession(
        user_id=_require_string(payload, "user_id", "whoami before revocation"),
        access_token=session.access_token,
        device_id=_require_string(payload, "device_id", "whoami before revocation"),
    )
    if not exact_identity_matches(
        confirmed,
        expected_user_id=expected_user_id,
        expected_device_id=session.device_id,
    ):
        raise PocError("whoami identity or device diverged from the authorized target")


def _admin_path(user_id: str) -> str:
    return f"{USER_ADMIN_PATH}/{quote(user_id, safe='')}"


def _device_path(user_id: str, device_id: str) -> str:
    return f"{_admin_path(user_id)}/devices/{quote(device_id, safe='')}"


def _admin_user(
    client: SafeHttpClient,
    admin_token: str,
    user_id: str,
) -> dict[str, object]:
    response = client.request("GET", _admin_path(user_id), token=admin_token)
    _require_status(response, 200, "admin user query")
    return _require_dict(response, "admin user query")


def _device_count(client: SafeHttpClient, admin_token: str, user_id: str) -> int:
    response = client.request(
        "GET",
        f"{_admin_path(user_id)}/devices",
        token=admin_token,
    )
    _require_status(response, 200, "device list")
    payload = _require_dict(response, "device list")
    devices = payload.get("devices")
    if not isinstance(devices, list):
        raise PocError("device list returned an invalid payload")
    return len(devices)


def _revoke_and_confirm(
    client: SafeHttpClient,
    *,
    admin_token: str,
    session: RegisteredSession,
) -> None:
    path = _device_path(session.user_id, session.device_id)
    before = client.request("GET", path, token=admin_token)
    _require_status(before, 200, "device query before revocation")
    before_payload = _require_dict(before, "device query before revocation")
    if (
        before_payload.get("user_id") != session.user_id
        or before_payload.get("device_id") != session.device_id
    ):
        raise PocError("device query diverged from the provisioned session")

    deleted = client.request("DELETE", path, token=admin_token, payload={})
    _require_status(deleted, 200, "device revocation")

    after = client.request("GET", path, token=admin_token)
    _require_status(after, 404, "device query after revocation")

    rejected = _whoami(client, session.access_token)
    _require_status(rejected, 401, "whoami after revocation")


def _login(
    client: SafeHttpClient,
    *,
    user_id: str,
    password: str,
    device_id: str,
) -> ApiResponse:
    return client.request(
        "POST",
        LOGIN_PATH,
        payload={
            "type": "m.login.password",
            "identifier": {"type": "m.id.user", "user": user_id},
            "password": password,
            "device_id": device_id,
            "initial_device_display_name": "Disposable create-only POC",
        },
    )


def _parse_login_session(
    response: ApiResponse,
    *,
    expected_user_id: str,
    expected_device_id: str,
    sensitive_values: dict[str, set[str]],
) -> RegisteredSession:
    _require_status(response, 200, "login with original password")
    payload = _require_dict(response, "login with original password")
    session = RegisteredSession(
        user_id=_require_string(payload, "user_id", "login with original password"),
        access_token=_require_string(
            payload,
            "access_token",
            "login with original password",
        ),
        device_id=_require_string(payload, "device_id", "login with original password"),
    )
    _record_sensitive(sensitive_values, "access_token", session.access_token)
    if not exact_identity_matches(
        session,
        expected_user_id=expected_user_id,
        expected_device_id=expected_device_id,
    ):
        raise PocError("login returned an unexpected identity or device")
    return session


def _logout_and_confirm(client: SafeHttpClient, session: RegisteredSession) -> None:
    response = client.request(
        "POST", LOGOUT_PATH, token=session.access_token, payload={}
    )
    _require_status(response, 200, "temporary admin logout")
    rejected = _whoami(client, session.access_token)
    _require_status(rejected, 401, "temporary admin whoami after logout")


def _verify_server_version(client: SafeHttpClient, admin_token: str) -> str:
    response = client.request("GET", SERVER_VERSION_PATH, token=admin_token)
    _require_status(response, 200, "server version")
    payload = _require_dict(response, "server version")
    version = _require_string(payload, "server_version", "server version")
    if version != EXPECTED_SYNAPSE_VERSION:
        raise PocError("disposable Synapse version diverged from the pinned version")
    return version


def _execute_http_poc(
    client: SafeHttpClient,
    *,
    shared_secret: str,
    sensitive_values: dict[str, set[str]],
) -> dict[str, object]:
    suffix = secrets.token_hex(6)
    admin_username = f"pocadmin{suffix}"
    target_username = f"poctarget{suffix}"
    target_user_id = f"@{target_username}:{SERVER_NAME}"
    admin_password = secrets.token_urlsafe(32)
    original_password = secrets.token_urlsafe(32)
    alternate_password = secrets.token_urlsafe(32)
    for password in (admin_password, original_password, alternate_password):
        _record_sensitive(sensitive_values, "password", password)

    admin_response = _registration_request(
        client,
        shared_secret=shared_secret,
        username=admin_username,
        password=admin_password,
        admin=True,
        sensitive_values=sensitive_values,
    )
    admin_session = _parse_registered_session(
        admin_response,
        operation="disposable admin registration",
        sensitive_values=sensitive_values,
    )
    _assert_whoami(client, admin_session, expected_user_id=admin_session.user_id)
    version = _verify_server_version(client, admin_session.access_token)
    admin_account = _admin_user(
        client,
        admin_session.access_token,
        admin_session.user_id,
    )
    if admin_account.get("admin") is not True:
        raise PocError("disposable bootstrap account is not a server admin")

    target_response = _registration_request(
        client,
        shared_secret=shared_secret,
        username=target_username,
        password=original_password,
        admin=False,
        sensitive_values=sensitive_values,
    )
    target_session = _parse_registered_session(
        target_response,
        operation="target registration",
        sensitive_values=sensitive_values,
    )
    if not exact_identity_matches(
        target_session,
        expected_user_id=target_user_id,
        expected_device_id=target_session.device_id,
    ):
        raise PocError("registered user diverged from the authorized target")
    _assert_whoami(client, target_session, expected_user_id=target_user_id)

    target_before = _admin_user(
        client,
        admin_session.access_token,
        target_user_id,
    )
    if target_before.get("admin") is not False:
        raise PocError("target registration unexpectedly created an admin")
    target_snapshot = stable_account_snapshot(target_before)

    _revoke_and_confirm(
        client,
        admin_token=admin_session.access_token,
        session=target_session,
    )
    devices_before_duplicate = _device_count(
        client,
        admin_session.access_token,
        target_user_id,
    )
    if devices_before_duplicate != 0:
        raise PocError("target retained a device after session revocation")

    duplicate_response = _registration_request(
        client,
        shared_secret=shared_secret,
        username=target_username,
        password=alternate_password,
        admin=False,
        sensitive_values=sensitive_values,
    )
    if duplicate_response.status != 400:
        raise PocError("existing identity did not produce the expected conflict")
    duplicate_payload = _require_dict(duplicate_response, "existing identity conflict")
    if duplicate_payload.get("errcode") != "M_USER_IN_USE":
        raise PocError("existing identity returned an unexpected conflict code")

    target_after = _admin_user(
        client,
        admin_session.access_token,
        target_user_id,
    )
    if stable_account_snapshot(target_after) != target_snapshot:
        raise PocError(
            "existing account properties changed after duplicate registration"
        )
    devices_after_duplicate = _device_count(
        client,
        admin_session.access_token,
        target_user_id,
    )
    if devices_after_duplicate != devices_before_duplicate:
        raise PocError("duplicate registration created an unexpected device")

    wrong_login = _login(
        client,
        user_id=target_user_id,
        password=alternate_password,
        device_id=f"WRONG{suffix.upper()}",
    )
    if wrong_login.status not in {401, 403}:
        raise PocError("alternate password was not rejected")

    login_device_id = f"POC{suffix.upper()}"
    original_login = _login(
        client,
        user_id=target_user_id,
        password=original_password,
        device_id=login_device_id,
    )
    login_session = _parse_login_session(
        original_login,
        expected_user_id=target_user_id,
        expected_device_id=login_device_id,
        sensitive_values=sensitive_values,
    )
    _revoke_and_confirm(
        client,
        admin_token=admin_session.access_token,
        session=login_session,
    )

    _logout_and_confirm(client, admin_session)

    return {
        "synapse_version": version,
        "server_name": SERVER_NAME,
        "checks": {
            "registration_returned_200": True,
            "target_identity_matched_exactly": True,
            "target_domain_matched": True,
            "target_whoami_returned_200_with_expected_device": True,
            "target_was_not_server_admin": True,
            "provisioning_device_returned_404_after_delete": True,
            "provisioning_token_returned_401_after_delete": True,
            "existing_identity_returned_m_user_in_use": True,
            "existing_account_properties_unchanged": True,
            "existing_account_device_count_unchanged": True,
            "alternate_password_rejected": True,
            "original_password_remained_valid": True,
            "temporary_admin_session_revoked": True,
        },
    }


def _docker_resources_removed(project_name: str) -> bool:
    try:
        containers = subprocess.run(
            [
                "docker",
                "ps",
                "--all",
                "--quiet",
                "--filter",
                f"label=com.docker.compose.project={project_name}",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        volumes = subprocess.run(
            [
                "docker",
                "volume",
                "ls",
                "--quiet",
                "--filter",
                f"label=com.docker.compose.project={project_name}",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        networks = subprocess.run(
            [
                "docker",
                "network",
                "ls",
                "--quiet",
                "--filter",
                f"label=com.docker.compose.project={project_name}",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return (
        containers.returncode == 0
        and volumes.returncode == 0
        and networks.returncode == 0
        and not containers.stdout.strip()
        and not volumes.stdout.strip()
        and not networks.stdout.strip()
    )


def run_poc() -> dict[str, object]:
    """Cria, valida e remove integralmente a stack descartável."""

    if shutil.which("docker") is None:
        raise PocError("Docker is required")

    project_name = f"social-interno-registration-poc-{secrets.token_hex(4)}"
    runtime_dir = Path(
        tempfile.mkdtemp(prefix="social-interno-registration-poc-")
    ).resolve()
    port = _free_local_port()
    postgres_password = secrets.token_urlsafe(32)
    registration_secret = secrets.token_urlsafe(48)
    macaroon_secret = secrets.token_urlsafe(48)
    form_secret = secrets.token_urlsafe(48)
    sensitive_values: dict[str, set[str]] = {}
    for category, value in (
        ("postgres_password", postgres_password),
        ("registration_shared_secret", registration_secret),
        ("macaroon_secret", macaroon_secret),
        ("form_secret", form_secret),
    ):
        _record_sensitive(sensitive_values, category, value)

    try:
        registration_secret_file = _write_runtime(
            runtime_dir,
            postgres_password=postgres_password,
            registration_secret=registration_secret,
            macaroon_secret=macaroon_secret,
            form_secret=form_secret,
        )
    except OSError:
        shutil.rmtree(runtime_dir, ignore_errors=True)
        raise PocError("could not prepare the disposable runtime") from None
    environment = os.environ.copy()
    environment.update(
        {
            "POC_POSTGRES_PASSWORD": postgres_password,
            "POC_REGISTRATION_SHARED_SECRET_FILE": str(registration_secret_file),
            "POC_RUNTIME_DIR": str(runtime_dir),
            "POC_SYNAPSE_PORT": str(port),
        }
    )

    client = SafeHttpClient(f"http://127.0.0.1:{port}")
    report: dict[str, object] | None = None
    failure: PocError | None = None
    logs_inspected = False
    logs_sanitized = False
    debug_logs_absent = False
    teardown_succeeded = False
    try:
        log_configuration = LOG_CONFIG_FILE.read_text(encoding="utf-8")
        if "level: DEBUG" in log_configuration:
            raise PocError("disposable Synapse logging is not safely configured")
        print("Starting isolated disposable Synapse stack...", file=sys.stderr)
        _run_command(
            _compose_command(
                project_name,
                "run",
                "--rm",
                "--no-deps",
                "synapse",
                "run",
                "--generate-keys",
            ),
            environment=environment,
        )
        _run_command(
            _compose_command(project_name, "up", "--detach"),
            environment=environment,
        )
        _wait_for_synapse(client)
        report = _execute_http_poc(
            client,
            shared_secret=registration_secret,
            sensitive_values=sensitive_values,
        )
    except PocError as error:
        failure = error
    except Exception:
        failure = PocError("unexpected POC failure")
    finally:
        logs_result = _run_command(
            _compose_command(project_name, "logs", "--no-color"),
            environment=environment,
            check=False,
        )
        if logs_result.returncode == 0:
            logs_inspected = True
            combined_logs = f"{logs_result.stdout}\n{logs_result.stderr}"
            leaked_categories = sensitive_categories_in_text(
                combined_logs,
                sensitive_values,
            )
            logs_sanitized = not leaked_categories
            debug_logs_absent = " - DEBUG - " not in combined_logs
            if leaked_categories:
                failure = PocError(
                    "sensitive categories found in logs: "
                    + ", ".join(leaked_categories)
                )
            elif not debug_logs_absent:
                failure = PocError("DEBUG entries found in disposable Synapse logs")

        down_result = _run_command(
            _compose_command(
                project_name,
                "down",
                "--volumes",
                "--remove-orphans",
                "--timeout",
                "10",
            ),
            environment=environment,
            check=False,
        )
        shutil.rmtree(runtime_dir, ignore_errors=True)
        teardown_succeeded = (
            down_result.returncode == 0
            and not runtime_dir.exists()
            and _docker_resources_removed(project_name)
        )

    if failure is not None:
        raise failure
    if report is None:
        raise PocError("POC produced no report")
    if not logs_inspected or not logs_sanitized or not debug_logs_absent:
        raise PocError("container logs were not safely inspected")
    if not teardown_succeeded:
        raise PocError("disposable Docker resources were not fully removed")

    checks_value = report.get("checks")
    if not isinstance(checks_value, dict) or not all(
        isinstance(key, str) and isinstance(value, bool)
        for key, value in checks_value.items()
    ):
        raise PocError("POC produced an invalid checks report")
    checks = cast(dict[str, bool], checks_value)
    report["checks"] = {
        **checks,
        "sensitive_container_logs_absent": True,
        "debug_logging_disabled": True,
        "disposable_containers_removed": True,
        "disposable_volumes_removed": True,
        "disposable_networks_removed": True,
        "temporary_runtime_removed": True,
    }
    report["status"] = "passed"
    report["environment"] = "disposable-local-only"
    report["images"] = {
        "synapse": SYNAPSE_IMAGE,
        "postgres": "postgres:17.6-alpine",
    }
    return report


def main() -> int:
    try:
        report = run_poc()
    except PocError as error:
        print(f"POC failed safely: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
