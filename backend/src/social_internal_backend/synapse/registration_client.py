"""Registro create-only do Synapse por segredo compartilhado."""

import hashlib
import hmac
from dataclasses import dataclass, field
from types import TracebackType
from typing import Any, Self

import httpx
from pydantic import SecretStr

from social_internal_backend.matrix import validate_matrix_user_id

REGISTRATION_PATH = "/_synapse/admin/v1/register"
MAX_SECRET_LENGTH = 4096
MAX_PASSWORD_LENGTH = 128


class SynapseRegistrationUnavailableError(Exception):
    """O endpoint de registro não pôde responder com segurança."""

    def __init__(self, *, ambiguous: bool = False) -> None:
        super().__init__("Synapse registration unavailable")
        self.ambiguous = ambiguous


class SynapseRegistrationProtocolError(Exception):
    """O endpoint de registro respondeu fora do contrato esperado."""

    def __init__(self, *, ambiguous: bool = False) -> None:
        super().__init__("Invalid Synapse registration response")
        self.ambiguous = ambiguous


class SynapseRegistrationConflictError(Exception):
    """A identidade já existe e não pode ser modificada pela ativação."""


@dataclass(slots=True)
class ProvisioningSession:
    """Sessão efêmera que nunca deve ser persistida ou representada com token."""

    user_id: str
    device_id: str
    access_token: SecretStr = field(repr=False)


def compute_registration_mac(
    shared_secret: str,
    nonce: str,
    username: str,
    password: str,
) -> str:
    """Calcula o HMAC documentado pelo Synapse para uma conta não administrativa."""

    message = b"\x00".join(
        (
            nonce.encode(),
            username.encode(),
            password.encode(),
            b"notadmin",
        )
    )
    return hmac.new(shared_secret.encode(), message, hashlib.sha1).hexdigest()


class SynapseRegistrationClient:
    """Cria exclusivamente contas novas e devolve a sessão efêmera resultante."""

    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float,
        shared_secret: SecretStr,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        secret = shared_secret.get_secret_value()
        if not secret or len(secret) > MAX_SECRET_LENGTH:
            raise ValueError("invalid Synapse registration shared secret")
        self._shared_secret = shared_secret
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
        self._client.close()

    def register(self, *, username: str, password: SecretStr) -> ProvisioningSession:
        """Executa nonce e registro create-only sem conservar senha, MAC ou nonce."""

        password_value = password.get_secret_value()
        if not 15 <= len(password_value) <= MAX_PASSWORD_LENGTH:
            raise ValueError("password must contain between 15 and 128 characters")
        nonce_response = self._request("GET")
        self._require_status(nonce_response, 200)
        nonce = self._required_string(nonce_response, "nonce")
        mac = compute_registration_mac(
            self._shared_secret.get_secret_value(),
            nonce,
            username,
            password_value,
        )
        try:
            response = self._request(
                "POST",
                json={
                    "nonce": nonce,
                    "username": username,
                    "password": password_value,
                    "admin": False,
                    "mac": mac,
                },
            )
        except SynapseRegistrationUnavailableError:
            raise SynapseRegistrationUnavailableError(ambiguous=True) from None
        if response.status_code in {400, 409}:
            payload = self._payload(response)
            if payload.get("errcode") == "M_USER_IN_USE":
                raise SynapseRegistrationConflictError
            raise SynapseRegistrationProtocolError(ambiguous=True)
        try:
            self._require_status(response, 200)
        except SynapseRegistrationProtocolError:
            raise SynapseRegistrationProtocolError(ambiguous=True) from None
        payload = self._payload(response)
        try:
            user_id = validate_matrix_user_id(self._required_value(payload, "user_id"))
        except ValueError:
            raise SynapseRegistrationProtocolError from None
        return ProvisioningSession(
            user_id=user_id,
            device_id=self._required_value(payload, "device_id"),
            access_token=SecretStr(self._required_value(payload, "access_token")),
        )

    def _request(
        self,
        method: str,
        *,
        json: dict[str, object] | None = None,
    ) -> httpx.Response:
        try:
            return self._client.request(method, REGISTRATION_PATH, json=json)
        except httpx.RequestError:
            raise SynapseRegistrationUnavailableError from None

    @staticmethod
    def _require_status(response: httpx.Response, expected: int) -> None:
        if response.status_code >= 500 or response.status_code in {401, 403, 429}:
            raise SynapseRegistrationUnavailableError
        if response.status_code != expected:
            raise SynapseRegistrationProtocolError

    @staticmethod
    def _payload(response: httpx.Response) -> dict[str, Any]:
        try:
            payload: Any = response.json()
        except ValueError:
            raise SynapseRegistrationProtocolError from None
        if not isinstance(payload, dict):
            raise SynapseRegistrationProtocolError
        return payload

    @classmethod
    def _required_string(cls, response: httpx.Response, field_name: str) -> str:
        return cls._required_value(cls._payload(response), field_name)

    @staticmethod
    def _required_value(payload: dict[str, Any], field_name: str) -> str:
        value = payload.get(field_name)
        if not isinstance(value, str) or not value:
            raise SynapseRegistrationProtocolError
        return value
