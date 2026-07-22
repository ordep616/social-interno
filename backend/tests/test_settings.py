"""Validação da configuração por ambiente."""

import pytest

from social_internal_backend.settings import Settings, get_settings


def configure_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Define somente valores fictícios usados pelos testes."""

    monkeypatch.setenv("BACKEND_ENVIRONMENT", "test")
    monkeypatch.setenv(
        "BACKEND_DATABASE_URL",
        "postgresql+psycopg://test:test@127.0.0.1:5433/test",
    )
    monkeypatch.setenv(
        "BACKEND_SYNAPSE_BASE_URL",
        "http://127.0.0.1:8008",
    )


def test_settings_load_prefixed_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_environment(monkeypatch)
    settings = Settings(_env_file=None)

    assert settings.environment == "test"
    assert str(settings.database_url).startswith("postgresql+psycopg://")


def test_get_settings_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_environment(monkeypatch)
    get_settings.cache_clear()

    first = get_settings()
    second = get_settings()

    assert first is second
    get_settings.cache_clear()
