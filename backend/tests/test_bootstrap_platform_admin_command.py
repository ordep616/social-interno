"""Interface local do bootstrap administrativo."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from social_internal_backend.authorization import BootstrapAlreadyCompletedError, BootstrapResult
from social_internal_backend.commands import bootstrap_platform_admin as command
from social_internal_backend.models import UserRole, UserRoleAssignment


def make_result(*, created: bool = True) -> BootstrapResult:
    assignment = UserRoleAssignment(
        matrix_user_id="@admin:localhost",
        role=UserRole.platform_admin,
        granted_at=datetime(2026, 7, 22, 16, tzinfo=UTC),
        granted_by=None,
    )
    return BootstrapResult(assignment=assignment, created=created)


def configure_command(monkeypatch: pytest.MonkeyPatch, outcome: object) -> MagicMock:
    engine = MagicMock()
    session = MagicMock()
    session_factory = MagicMock()
    session_factory.return_value.__enter__.return_value = session
    service = MagicMock()
    if isinstance(outcome, Exception):
        service.bootstrap.side_effect = outcome
    else:
        service.bootstrap.return_value = outcome

    monkeypatch.setattr(command, "get_settings", MagicMock(return_value=object()))
    monkeypatch.setattr(command, "build_engine", MagicMock(return_value=engine))
    monkeypatch.setattr(command, "build_session_factory", MagicMock(return_value=session_factory))
    monkeypatch.setattr(command, "PlatformAdminBootstrapService", MagicMock(return_value=service))
    return engine


@pytest.mark.parametrize(
    ("outcome", "expected_code", "expected_message"),
    [
        (make_result(), 0, "criada"),
        (make_result(created=False), 0, "já existente"),
        (ValueError(), 2, "inválida"),
        (BootstrapAlreadyCompletedError(), 1, "outra identidade"),
        (SQLAlchemyError(), 3, "banco próprio"),
    ],
)
def test_command_reports_sanitized_result(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    outcome: object,
    expected_code: int,
    expected_message: str,
) -> None:
    engine = configure_command(monkeypatch, outcome)

    assert command.main(["@admin:localhost"]) == expected_code
    captured = capsys.readouterr()
    assert expected_message in captured.out + captured.err
    engine.dispose.assert_called_once_with()


def test_parser_accepts_only_matrix_user_id() -> None:
    args = command.build_parser().parse_args(["@admin:localhost"])

    assert args.matrix_user_id == "@admin:localhost"
