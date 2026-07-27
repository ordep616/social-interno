"""Comportamento operacional da limpeza do limitador."""

from contextlib import AbstractContextManager
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from social_internal_backend.commands import cleanup_activation_rate_limits


def test_cleanup_commits_transaction_and_reports_sanitized_count(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    engine = MagicMock()
    session = MagicMock(spec=Session)
    transaction = MagicMock(spec=AbstractContextManager)
    transaction.__enter__.return_value = session
    session_factory = MagicMock()
    session_factory.begin.return_value = transaction
    repository = MagicMock()
    repository.delete_expired.return_value = 3

    monkeypatch.setattr(cleanup_activation_rate_limits, "get_settings", MagicMock())
    monkeypatch.setattr(
        cleanup_activation_rate_limits, "build_engine", MagicMock(return_value=engine)
    )
    monkeypatch.setattr(
        cleanup_activation_rate_limits,
        "build_session_factory",
        MagicMock(return_value=session_factory),
    )
    monkeypatch.setattr(
        cleanup_activation_rate_limits,
        "ActivationRateLimitRepository",
        MagicMock(return_value=repository),
    )

    assert cleanup_activation_rate_limits.main() == 0
    assert capsys.readouterr().out == "Contadores de ativação removidos: 3.\n"
    transaction.__exit__.assert_called_once()
    engine.dispose.assert_called_once_with()


def test_cleanup_fails_closed_without_database_details(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    engine = MagicMock()
    session_factory = MagicMock()
    session_factory.begin.side_effect = SQLAlchemyError("sensitive database detail")

    monkeypatch.setattr(cleanup_activation_rate_limits, "get_settings", MagicMock())
    monkeypatch.setattr(
        cleanup_activation_rate_limits, "build_engine", MagicMock(return_value=engine)
    )
    monkeypatch.setattr(
        cleanup_activation_rate_limits,
        "build_session_factory",
        MagicMock(return_value=session_factory),
    )

    assert cleanup_activation_rate_limits.main() == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "Falha ao limpar os limites de ativação.\n"
    assert "sensitive" not in captured.err
    engine.dispose.assert_called_once_with()
