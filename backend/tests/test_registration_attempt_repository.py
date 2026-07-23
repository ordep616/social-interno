"""Contrato SQLAlchemy do repositório de tentativas de cadastro."""

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

from sqlalchemy.orm import Session

from social_internal_backend.models import (
    InvitationRole,
    RegistrationAttempt,
    RegistrationAttemptStatus,
)
from social_internal_backend.registrations import RegistrationAttemptRepository


def make_attempt(
    *,
    status: RegistrationAttemptStatus = RegistrationAttemptStatus.processing,
) -> RegistrationAttempt:
    now = datetime(2026, 7, 23, 12, tzinfo=UTC)
    return RegistrationAttempt(
        id=uuid4(),
        invitation_id=uuid4(),
        matrix_user_id="@alice:localhost",
        role=InvitationRole.user,
        status=status,
        created_at=now,
        updated_at=now,
    )


def test_adds_flushes_and_gets_attempt_without_committing() -> None:
    session = MagicMock(spec=Session)
    repository = RegistrationAttemptRepository(session)
    attempt = make_attempt()
    session.get.return_value = attempt

    assert repository.add(attempt) is attempt
    assert repository.get(attempt.id) is attempt

    session.add.assert_called_once_with(attempt)
    session.flush.assert_called_once_with()
    session.get.assert_called_once_with(RegistrationAttempt, attempt.id)
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_queries_active_attempt_by_invitation_and_identity() -> None:
    session = MagicMock(spec=Session)
    repository = RegistrationAttemptRepository(session)
    attempt = make_attempt()
    session.scalars.return_value.one_or_none.return_value = attempt

    assert repository.get_active_by_invitation(attempt.invitation_id) is attempt
    assert repository.get_active_by_matrix_user_id(attempt.matrix_user_id) is attempt

    assert session.scalars.call_count == 2
    session.commit.assert_not_called()
    session.rollback.assert_not_called()


def test_executes_all_conditional_transitions_without_committing() -> None:
    session = MagicMock(spec=Session)
    repository = RegistrationAttemptRepository(session)
    attempt = make_attempt()
    now = datetime(2026, 7, 23, 13, tzinfo=UTC)
    session.execute.return_value.scalar_one_or_none.return_value = attempt

    assert repository.mark_synapse_created(attempt.id, now) is attempt
    assert repository.mark_completed(attempt.id, now) is attempt
    assert (
        repository.mark_released(
            attempt.id,
            failure_code="username_unavailable",
            now=now,
        )
        is attempt
    )
    assert (
        repository.mark_reconciliation_required(
            attempt.id,
            failure_code="synapse_result_ambiguous",
            now=now,
        )
        is attempt
    )

    assert session.execute.call_count == 4
    session.commit.assert_not_called()
    session.rollback.assert_not_called()
