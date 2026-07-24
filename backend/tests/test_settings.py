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
    monkeypatch.setenv("BACKEND_MATRIX_SERVER_NAME", "localhost")
    monkeypatch.setenv(
        "BACKEND_SYNAPSE_BASE_URL",
        "http://127.0.0.1:8008",
    )
    monkeypatch.setenv(
        "BACKEND_SYNAPSE_ADMIN_ACCESS_TOKEN",
        "opaque-admin-value-for-tests",
    )
    monkeypatch.setenv(
        "BACKEND_INVITATION_PUBLIC_BASE_URL",
        "http://127.0.0.1:8080/activate",
    )


def test_settings_load_prefixed_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_environment(monkeypatch)
    settings = Settings(_env_file=None)

    assert settings.environment == "test"
    assert str(settings.database_url).startswith("postgresql+psycopg://")
    assert settings.matrix_server_name == "localhost"
    assert settings.synapse_request_timeout_seconds == 5
    assert settings.synapse_admin_access_token.get_secret_value() == (
        "opaque-admin-value-for-tests"
    )
    assert "opaque-admin-value-for-tests" not in repr(settings)
    assert str(settings.invitation_public_base_url).endswith("/activate")
    assert "http://127.0.0.1:8080" in settings.cors_allowed_origins


def test_settings_reject_invalid_synapse_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_environment(monkeypatch)
    monkeypatch.setenv("BACKEND_SYNAPSE_REQUEST_TIMEOUT_SECONDS", "0")

    with pytest.raises(ValueError):
        Settings(_env_file=None)


@pytest.mark.parametrize(
    ("public_url", "expected_error"),
    [
        (
            "http://127.0.0.1:8080/activate?token=forbidden",
            "query or fragment",
        ),
        (
            "http://127.0.0.1:8080/activate#forbidden",
            "query or fragment",
        ),
        (
            "http://user:password@127.0.0.1:8080/activate",
            "credentials",
        ),
        (
            "http://127.0.0.1:8080/register",
            "activation route",
        ),
    ],
)
def test_settings_reject_unsafe_invitation_public_url(
    monkeypatch: pytest.MonkeyPatch,
    public_url: str,
    expected_error: str,
) -> None:
    configure_environment(monkeypatch)
    monkeypatch.setenv("BACKEND_INVITATION_PUBLIC_BASE_URL", public_url)

    with pytest.raises(ValueError, match=expected_error):
        Settings(_env_file=None)


def test_settings_reject_matrix_server_name_formatted_as_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_environment(monkeypatch)
    monkeypatch.setenv("BACKEND_MATRIX_SERVER_NAME", "https://matrix.example")

    with pytest.raises(ValueError, match="Matrix server name"):
        Settings(_env_file=None)


def test_get_settings_is_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_environment(monkeypatch)
    get_settings.cache_clear()

    first = get_settings()
    second = get_settings()

    assert first is second
    get_settings.cache_clear()
