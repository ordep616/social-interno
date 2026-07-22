"""Fixtures compartilhadas pelos testes."""

from collections.abc import AsyncIterator

import httpx
import pytest

from social_internal_backend.application import create_app
from social_internal_backend.settings import Settings


@pytest.fixture
def settings() -> Settings:
    """Fornece configuração isolada sem ler um arquivo local."""

    return Settings(
        _env_file=None,
        environment="test",
        database_url="postgresql+psycopg://test:test@127.0.0.1:5433/test",
        synapse_base_url="http://127.0.0.1:8008",
    )


@pytest.fixture
def anyio_backend() -> str:
    """Executa testes assíncronos somente com asyncio."""

    return "asyncio"


@pytest.fixture
async def client(settings: Settings) -> AsyncIterator[httpx.AsyncClient]:
    """Cria um cliente sem iniciar banco ou Synapse."""

    transport = httpx.ASGITransport(app=create_app(settings))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client
