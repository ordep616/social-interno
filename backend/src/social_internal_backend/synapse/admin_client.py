"""Cliente mínimo da API administrativa de usuários do Synapse."""

from dataclasses import dataclass
from types import TracebackType
from typing import Any, Self
from urllib.parse import quote

import httpx
from pydantic import SecretStr

from social_internal_backend.matrix import validate_matrix_user_id

USER_ADMIN_PATH = "/_synapse/admin/v2/users"
USER_DEACTIVATE_PATH = "/_synapse/admin/v1/deactivate"
USER_RESET_PASSWORD_PATH = "/_synapse/admin/v1/reset_password"  # noqa: S105
MAX_ADMIN_ACCESS_TOKEN_LENGTH = 4096
MAX_PASSWORD_LENGTH = 512
MAX_DISPLAY_NAME_LENGTH = 255
MAX_USER_LIST_LIMIT = 100


class InvalidSynapseAdminCredentialError(Exception):
    """A credencial administrativa está ausente, inválida ou foi recusada."""


class SynapseAdminRateLimitedError(Exception):
    """O Synapse limitou temporariamente a operação administrativa."""


class SynapseAdminUnavailableError(Exception):
    """A API administrativa do Synapse não pôde responder."""


class SynapseAdminProtocolError(Exception):
    """O Synapse respondeu fora do contrato administrativo esperado."""


class SynapseUserNotFoundError(Exception):
    """A conta local consultada não existe."""


class SynapseUserAlreadyExistsError(Exception):
    """A criação encontrou uma conta existente ou um resultado ambíguo."""


@dataclass(frozen=True, slots=True)
class SynapseUser:
    """Estado mínimo de uma conta sem dados pessoais opcionais."""

    user_id: str
    display_name: str | None
    admin: bool
    deactivated: bool
    locked: bool
    suspended: bool


@dataclass(frozen=True, slots=True)
class SynapseUserPage:
    """Página de contas locais retornada pela API administrativa."""

    users: tuple[SynapseUser, ...]
    total: int
    next_token: str | None


@dataclass(frozen=True, slots=True)
class CreatedSynapseUser:
    """Confirma uma criação sem conservar senha ou credencial."""

    user_id: str


class SynapseAdminClient:
    """Consulta e cria contas locais com uma credencial exclusiva do servidor."""

    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float,
        matrix_server_name: str,
        admin_access_token: SecretStr,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not 0 < timeout_seconds <= 30:
            raise ValueError("timeout_seconds must be greater than zero and at most 30")
        self._matrix_server_name = self._validate_server_name(matrix_server_name)
        self._admin_access_token = self._validate_admin_access_token(admin_access_token)
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=False,
            trust_env=False,
            transport=transport,
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_type, exc_value, traceback
        self.close()

    def close(self) -> None:
        """Libera conexões mantidas pelo cliente administrativo."""

        self._client.close()

    def get_user(self, user_id: str) -> SynapseUser:
        """Consulta uma conta local sem acessar diretamente o banco do Synapse."""

        validated_user_id = self._validate_local_user_id(user_id)
        response = self._request("GET", self._user_path(validated_user_id))
        if response.status_code == 404:
            raise SynapseUserNotFoundError
        self._raise_common_error(response, expected_status=200)
        return self._parse_user(response, expected_user_id=validated_user_id)

    def list_users(
        self,
        *,
        offset: int = 0,
        limit: int = MAX_USER_LIST_LIMIT,
        query: str | None = None,
    ) -> SynapseUserPage:
        """Lista contas locais por meio da API administrativa suportada."""

        if offset < 0:
            raise ValueError("offset must not be negative")
        if not 1 <= limit <= MAX_USER_LIST_LIMIT:
            raise ValueError(f"limit must be between 1 and {MAX_USER_LIST_LIMIT}")

        params: dict[str, str] = {
            "from": str(offset),
            "limit": str(limit),
            "guests": "false",
            "deactivated": "true",
            "locked": "true",
        }
        if query is not None and query.strip():
            params["name"] = query.strip()

        response = self._request("GET", USER_ADMIN_PATH, params=params)
        self._raise_common_error(response, expected_status=200)
        return self._parse_user_page(response)

    def create_user(
        self,
        *,
        user_id: str,
        password: SecretStr,
    ) -> CreatedSynapseUser:
        """Cria uma conta não administrativa depois de uma consulta preventiva."""

        validated_user_id = self._validate_local_user_id(user_id)
        password_value = password.get_secret_value()
        if not password_value or len(password_value) > MAX_PASSWORD_LENGTH:
            raise ValueError("password must contain between 1 and 512 characters")

        try:
            self.get_user(validated_user_id)
        except SynapseUserNotFoundError:
            pass
        else:
            raise SynapseUserAlreadyExistsError

        response = self._request(
            "PUT",
            self._user_path(validated_user_id),
            json={
                "password": password_value,
                "admin": False,
                "deactivated": False,
                "locked": False,
            },
        )
        if response.status_code in {200, 409}:
            raise SynapseUserAlreadyExistsError
        self._raise_common_error(response, expected_status=201)
        return CreatedSynapseUser(user_id=validated_user_id)

    def update_user(
        self,
        *,
        user_id: str,
        display_name: str | None = None,
        locked: bool | None = None,
    ) -> SynapseUser:
        """Atualiza campos administrativos permitidos sem criar conta nova."""

        validated_user_id = self._validate_local_user_id(user_id)
        if display_name is None and locked is None:
            raise ValueError("at least one account field must be provided")
        if display_name is not None and len(display_name) > MAX_DISPLAY_NAME_LENGTH:
            raise ValueError("display_name must be at most 255 characters")

        current = self.get_user(validated_user_id)
        body: dict[str, object] = {"admin": current.admin}
        if display_name is not None:
            body["displayname"] = display_name
        if locked is not None:
            body["locked"] = locked

        response = self._request("PUT", self._user_path(validated_user_id), json=body)
        if response.status_code == 404:
            raise SynapseUserNotFoundError
        self._raise_common_error(response, expected_status=200)
        return self.get_user(validated_user_id)

    def reset_password(
        self,
        *,
        user_id: str,
        new_password: SecretStr,
        logout_devices: bool = True,
    ) -> None:
        """Redefine senha pela API administrativa sem persistir o segredo."""

        validated_user_id = self._validate_local_user_id(user_id)
        password_value = new_password.get_secret_value()
        if not password_value or len(password_value) > MAX_PASSWORD_LENGTH:
            raise ValueError("password must contain between 1 and 512 characters")

        response = self._request(
            "POST",
            self._reset_password_path(validated_user_id),
            json={
                "new_password": password_value,
                "logout_devices": logout_devices,
            },
        )
        if response.status_code == 404:
            raise SynapseUserNotFoundError
        self._raise_common_error(response, expected_status=200)

    def deactivate_user(self, *, user_id: str, erase: bool) -> None:
        """Desativa uma conta local; `erase` equivale à exclusão lógica forte."""

        validated_user_id = self._validate_local_user_id(user_id)
        response = self._request(
            "POST",
            self._deactivate_path(validated_user_id),
            json={"erase": erase},
        )
        if response.status_code == 404:
            raise SynapseUserNotFoundError
        self._raise_common_error(response, expected_status=200)

    def get_device(self, *, user_id: str, device_id: str) -> None:
        """Confirma que o dispositivo pertence à conta provisionada."""

        response = self._request("GET", self._device_path(user_id, device_id))
        if response.status_code == 404:
            raise SynapseUserNotFoundError
        self._raise_common_error(response, expected_status=200)
        payload = response.json()
        if (
            not isinstance(payload, dict)
            or payload.get("user_id") != user_id
            or payload.get("device_id") != device_id
        ):
            raise SynapseAdminProtocolError

    def delete_device(self, *, user_id: str, device_id: str) -> None:
        """Revoga uma sessão de provisionamento pela API administrativa."""

        response = self._request(
            "DELETE",
            self._device_path(user_id, device_id),
            json={},
        )
        self._raise_common_error(response, expected_status=200)

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, object] | None = None,
        params: dict[str, str] | None = None,
    ) -> httpx.Response:
        try:
            return self._client.request(
                method,
                path,
                headers={
                    "Authorization": (f"Bearer {self._admin_access_token.get_secret_value()}")
                },
                json=json,
                params=params,
            )
        except httpx.RequestError:
            raise SynapseAdminUnavailableError from None

    @staticmethod
    def _raise_common_error(
        response: httpx.Response,
        *,
        expected_status: int,
    ) -> None:
        if response.status_code in {401, 403}:
            raise InvalidSynapseAdminCredentialError
        if response.status_code == 429:
            raise SynapseAdminRateLimitedError
        if response.status_code >= 500:
            raise SynapseAdminUnavailableError
        if response.status_code != expected_status:
            raise SynapseAdminProtocolError

    def _validate_local_user_id(self, user_id: str) -> str:
        validated_user_id = validate_matrix_user_id(user_id)
        _, server_name = validated_user_id[1:].split(":", maxsplit=1)
        if server_name != self._matrix_server_name:
            raise ValueError("Matrix user ID does not belong to the configured server")
        return validated_user_id

    def _device_path(self, user_id: str, device_id: str) -> str:
        validated_user_id = self._validate_local_user_id(user_id)
        if not device_id or len(device_id) > 255:
            raise ValueError("invalid device ID")
        return f"{self._user_path(validated_user_id)}/devices/{quote(device_id, safe='')}"

    @staticmethod
    def _validate_server_name(server_name: str) -> str:
        if (
            not server_name
            or len(server_name) > 255
            or "://" in server_name
            or "/" in server_name
            or any(character.isspace() or not character.isprintable() for character in server_name)
        ):
            raise ValueError("invalid Matrix server name")
        return server_name

    @staticmethod
    def _validate_admin_access_token(admin_access_token: SecretStr) -> SecretStr:
        token_value = admin_access_token.get_secret_value()
        if (
            not token_value
            or len(token_value) > MAX_ADMIN_ACCESS_TOKEN_LENGTH
            or any(character.isspace() or not character.isprintable() for character in token_value)
        ):
            raise InvalidSynapseAdminCredentialError
        return admin_access_token

    @staticmethod
    def _user_path(user_id: str) -> str:
        return f"{USER_ADMIN_PATH}/{quote(user_id, safe='')}"

    @staticmethod
    def _deactivate_path(user_id: str) -> str:
        return f"{USER_DEACTIVATE_PATH}/{quote(user_id, safe='')}"

    @staticmethod
    def _reset_password_path(user_id: str) -> str:
        return f"{USER_RESET_PASSWORD_PATH}/{quote(user_id, safe='')}"

    def _parse_user(
        self,
        response: httpx.Response,
        *,
        expected_user_id: str,
    ) -> SynapseUser:
        try:
            payload: Any = response.json()
        except ValueError:
            raise SynapseAdminProtocolError from None
        if not isinstance(payload, dict):
            raise SynapseAdminProtocolError

        return self._parse_user_payload(payload, expected_user_id=expected_user_id)

    def _parse_user_page(self, response: httpx.Response) -> SynapseUserPage:
        try:
            payload: Any = response.json()
        except ValueError:
            raise SynapseAdminProtocolError from None
        if not isinstance(payload, dict):
            raise SynapseAdminProtocolError

        users_payload = payload.get("users")
        total = payload.get("total")
        next_token = payload.get("next_token")
        if not isinstance(users_payload, list) or not isinstance(total, int):
            raise SynapseAdminProtocolError
        if next_token is not None and not isinstance(next_token, str):
            raise SynapseAdminProtocolError

        users = tuple(
            self._parse_user_payload(user_payload, expected_user_id=None)
            for user_payload in users_payload
        )
        return SynapseUserPage(users=users, total=total, next_token=next_token)

    def _parse_user_payload(
        self,
        payload: dict[str, Any],
        *,
        expected_user_id: str | None,
    ) -> SynapseUser:
        user_id = payload.get("name")
        display_name = payload.get("displayname")
        admin = payload.get("admin")
        deactivated = payload.get("deactivated")
        locked = payload.get("locked")
        suspended = payload.get("suspended", False)
        if (
            not isinstance(user_id, str)
            or not (display_name is None or isinstance(display_name, str))
            or not isinstance(admin, bool)
            or not isinstance(deactivated, bool)
            or not isinstance(locked, bool)
            or not isinstance(suspended, bool)
        ):
            raise SynapseAdminProtocolError
        try:
            validated_user_id = self._validate_local_user_id(user_id)
        except ValueError:
            raise SynapseAdminProtocolError from None
        if expected_user_id is not None and validated_user_id != expected_user_id:
            raise SynapseAdminProtocolError

        return SynapseUser(
            user_id=validated_user_id,
            display_name=display_name,
            admin=admin,
            deactivated=deactivated,
            locked=locked,
            suspended=suspended,
        )
