"""Cliente mínimo da API Client-Server usada para autenticação."""

from dataclasses import dataclass
from types import TracebackType
from typing import Any, Self

import httpx

from social_internal_backend.matrix import validate_matrix_user_id

WHOAMI_PATH = "/_matrix/client/v3/account/whoami"
MAX_ACCESS_TOKEN_LENGTH = 4096


class InvalidMatrixAccessTokenError(Exception):
    """O Synapse não reconheceu ou recusou a credencial Matrix."""


class SynapseRateLimitedError(Exception):
    """O Synapse limitou temporariamente a validação da credencial."""


class SynapseUnavailableError(Exception):
    """O Synapse não pôde responder à validação."""


class SynapseProtocolError(Exception):
    """O Synapse respondeu fora do contrato Matrix esperado."""


@dataclass(frozen=True, slots=True)
class MatrixIdentity:
    """Identidade autenticada sem conservar o token que a originou."""

    user_id: str
    is_guest: bool
    device_id: str | None


class SynapseClient:
    """Valida tokens no endpoint padrão `whoami` do homeserver configurado."""

    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not 0 < timeout_seconds <= 30:
            raise ValueError("timeout_seconds must be greater than zero and at most 30")
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
        """Libera conexões mantidas pelo cliente HTTP."""

        self._client.close()

    def whoami(self, access_token: str) -> MatrixIdentity:
        """Retorna a identidade do token sem enviá-lo na URL ou no corpo."""

        self._validate_access_token(access_token)
        try:
            response = self._client.get(
                WHOAMI_PATH,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        except httpx.RequestError:
            raise SynapseUnavailableError from None

        if response.status_code in {401, 403}:
            raise InvalidMatrixAccessTokenError
        if response.status_code == 429:
            raise SynapseRateLimitedError
        if response.status_code >= 500:
            raise SynapseUnavailableError
        if response.status_code != 200:
            raise SynapseProtocolError

        return self._parse_identity(response)

    @staticmethod
    def _validate_access_token(access_token: str) -> None:
        if (
            not access_token
            or len(access_token) > MAX_ACCESS_TOKEN_LENGTH
            or any(character.isspace() or not character.isprintable() for character in access_token)
        ):
            raise InvalidMatrixAccessTokenError

    @staticmethod
    def _parse_identity(response: httpx.Response) -> MatrixIdentity:
        try:
            payload: Any = response.json()
        except ValueError:
            raise SynapseProtocolError from None
        if not isinstance(payload, dict):
            raise SynapseProtocolError

        user_id = payload.get("user_id")
        is_guest = payload.get("is_guest", False)
        device_id = payload.get("device_id")
        if not isinstance(user_id, str) or not isinstance(is_guest, bool):
            raise SynapseProtocolError
        if device_id is not None and not isinstance(device_id, str):
            raise SynapseProtocolError
        try:
            validated_user_id = validate_matrix_user_id(user_id)
        except ValueError:
            raise SynapseProtocolError from None

        return MatrixIdentity(
            user_id=validated_user_id,
            is_guest=is_guest,
            device_id=device_id,
        )
