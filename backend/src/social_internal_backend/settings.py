"""Configuração validada do serviço."""

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, PostgresDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from social_internal_backend.matrix import validate_matrix_server_name


class Settings(BaseSettings):
    """Valores fornecidos exclusivamente pelo ambiente de execução."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="BACKEND_",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Literal["local", "test", "homologation", "production"] = "local"
    database_url: PostgresDsn
    matrix_server_name: str = Field(min_length=1, max_length=255)
    synapse_base_url: AnyHttpUrl
    synapse_request_timeout_seconds: float = Field(default=5.0, gt=0, le=30)
    synapse_admin_access_token: SecretStr
    synapse_registration_shared_secret: SecretStr
    invitation_public_base_url: AnyHttpUrl
    cors_allowed_origins: tuple[str, ...] = (
        "http://127.0.0.1:8080",
        "http://localhost:8080",
    )
    service_name: str = "social-interno-backend"

    @field_validator("matrix_server_name")
    @classmethod
    def validate_configured_matrix_server_name(cls, value: str) -> str:
        """Reutiliza a validação aplicada ao identificador corporativo."""

        return validate_matrix_server_name(value)

    @field_validator("invitation_public_base_url")
    @classmethod
    def validate_invitation_public_url(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        """Reserva query e fragmento exclusivamente para o fluxo de ativação."""

        if value.query is not None or value.fragment is not None:
            raise ValueError("invitation public base URL must not contain query or fragment")
        if value.username is not None or value.password is not None:
            raise ValueError("invitation public base URL must not contain credentials")
        if not (value.path or "").rstrip("/").endswith("/activate"):
            raise ValueError("invitation public base URL must point to the activation route")
        return value


@lru_cache
def get_settings() -> Settings:
    """Carrega a configuração uma vez por processo."""

    return Settings()
