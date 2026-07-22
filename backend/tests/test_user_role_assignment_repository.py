"""Acesso SQLAlchemy às atribuições de papéis."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from social_internal_backend.authorization.repository import UserRoleAssignmentRepository
from social_internal_backend.models import UserRole, UserRoleAssignment


def make_assignment() -> UserRoleAssignment:
    return UserRoleAssignment(
        matrix_user_id="@admin:localhost",
        role=UserRole.platform_admin,
        granted_at=datetime(2026, 7, 22, 16, tzinfo=UTC),
        granted_by=None,
    )


def test_locks_table_adds_flushes_and_gets_assignment() -> None:
    session = MagicMock(spec=Session)
    repository = UserRoleAssignmentRepository(session)
    assignment = make_assignment()
    session.get.return_value = assignment

    repository.lock_for_bootstrap()
    assert repository.add(assignment) is assignment
    assert repository.get(assignment.matrix_user_id) is assignment

    session.execute.assert_called_once()
    session.add.assert_called_once_with(assignment)
    session.flush.assert_called_once_with()
    session.get.assert_called_once_with(UserRoleAssignment, assignment.matrix_user_id)


def test_queries_first_platform_admin() -> None:
    session = MagicMock(spec=Session)
    repository = UserRoleAssignmentRepository(session)
    assignment = make_assignment()
    session.scalars.return_value.one_or_none.return_value = assignment

    assert repository.get_first_platform_admin() is assignment
    session.scalars.assert_called_once()
