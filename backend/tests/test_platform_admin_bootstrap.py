"""Regras do bootstrap local do primeiro administrador."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from social_internal_backend.authorization.bootstrap import (
    BootstrapAlreadyCompletedError,
    PlatformAdminBootstrapService,
    validate_matrix_user_id,
)
from social_internal_backend.models import UserRole, UserRoleAssignment

NOW = datetime(2026, 7, 22, 16, tzinfo=UTC)


def make_assignment(
    matrix_user_id: str = "@admin:localhost",
    role: UserRole = UserRole.platform_admin,
) -> UserRoleAssignment:
    return UserRoleAssignment(
        matrix_user_id=matrix_user_id,
        role=role,
        granted_at=NOW,
        granted_by=None,
    )


class FakeUserRoleAssignmentRepository:
    def __init__(self) -> None:
        self.locked = False
        self.added: UserRoleAssignment | None = None
        self.by_id: UserRoleAssignment | None = None
        self.first_admin: UserRoleAssignment | None = None
        self.raise_on_lock: Exception | None = None

    def lock_for_bootstrap(self) -> None:
        if self.raise_on_lock is not None:
            raise self.raise_on_lock
        self.locked = True

    def add(self, assignment: UserRoleAssignment) -> UserRoleAssignment:
        self.added = assignment
        return assignment

    def get(self, matrix_user_id: str) -> UserRoleAssignment | None:
        assert matrix_user_id == "@admin:localhost"
        return self.by_id

    def get_first_platform_admin(self) -> UserRoleAssignment | None:
        return self.first_admin


def make_service(
    repository: FakeUserRoleAssignmentRepository,
    session: MagicMock,
    *,
    now: datetime = NOW,
) -> PlatformAdminBootstrapService:
    return PlatformAdminBootstrapService(
        session,
        repository=repository,
        clock=lambda: now,
    )


@pytest.mark.parametrize(
    "invalid_user_id",
    [
        "admin:localhost",
        "@:localhost",
        "@admin:",
        "@admin local:localhost",
        "@admin",
        "@admin:\x00localhost",
    ],
)
def test_rejects_invalid_matrix_user_id(invalid_user_id: str) -> None:
    with pytest.raises(ValueError, match="invalid Matrix user ID"):
        validate_matrix_user_id(invalid_user_id)


def test_rejects_matrix_user_id_longer_than_database_column() -> None:
    with pytest.raises(ValueError, match="invalid Matrix user ID"):
        validate_matrix_user_id("@" + "a" * 244 + ":localhost.example")


def test_creates_first_platform_admin_and_commits() -> None:
    repository = FakeUserRoleAssignmentRepository()
    session = MagicMock(spec=Session)
    result = make_service(repository, session).bootstrap("@admin:localhost")

    assert repository.locked
    assert result.created
    assert result.assignment is repository.added
    assert result.assignment.role is UserRole.platform_admin
    assert result.assignment.granted_by is None
    session.commit.assert_called_once_with()


def test_promotes_existing_non_admin_only_during_first_bootstrap() -> None:
    repository = FakeUserRoleAssignmentRepository()
    repository.by_id = make_assignment(role=UserRole.user)
    session = MagicMock(spec=Session)
    result = make_service(repository, session).bootstrap("@admin:localhost")

    assert result.created
    assert result.assignment.role is UserRole.platform_admin
    assert repository.added is None
    session.commit.assert_called_once_with()


def test_same_platform_admin_is_idempotent() -> None:
    repository = FakeUserRoleAssignmentRepository()
    repository.by_id = make_assignment()
    session = MagicMock(spec=Session)
    result = make_service(repository, session).bootstrap("@admin:localhost")

    assert not result.created
    assert result.assignment is repository.by_id
    session.commit.assert_called_once_with()
    session.rollback.assert_not_called()


def test_rejects_different_admin_after_bootstrap_and_rolls_back() -> None:
    repository = FakeUserRoleAssignmentRepository()
    repository.first_admin = make_assignment("@existing:localhost")
    session = MagicMock(spec=Session)

    with pytest.raises(BootstrapAlreadyCompletedError):
        make_service(repository, session).bootstrap("@admin:localhost")
    session.rollback.assert_called_once_with()


def test_rolls_back_repository_failure_and_rejects_naive_clock() -> None:
    repository = FakeUserRoleAssignmentRepository()
    repository.raise_on_lock = RuntimeError("database failed")
    session = MagicMock(spec=Session)

    with pytest.raises(RuntimeError, match="database failed"):
        make_service(repository, session).bootstrap("@admin:localhost")
    session.rollback.assert_called_once_with()

    repository.raise_on_lock = None
    with pytest.raises(ValueError, match="timezone-aware"):
        make_service(repository, session, now=datetime(2026, 7, 22, 16)).bootstrap(
            "@admin:localhost"
        )
