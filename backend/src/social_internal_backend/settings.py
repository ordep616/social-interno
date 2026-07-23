"""Configuração validada do serviço."""

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    synapse_base_url: AnyHttpUrl
    synapse_request_timeout_seconds: float = Field(default=5.0, gt=0, le=30)
    service_name: str = "social-interno-backend"


@lru_cache
def get_settings() -> Settings:
    """Carrega a configuração uma vez por processo."""

    return Settings()
