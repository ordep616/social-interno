"""Contrato persistente dos papéis corporativos."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import CheckConstraint, Index, Table

from social_internal_backend.models import UserRole, UserRoleAssignment


def test_roles_include_platform_admin_without_changing_invitation_roles() -> None:
    assert {role.value for role in UserRole} == {
        "user",
        "group_admin",
        "platform_admin",
    }

    with pytest.raises(ValueError):
        UserRole("unknown")


def test_assignment_contains_only_role_metadata_for_matrix_identity() -> None:
    assert set(UserRoleAssignment.__table__.columns.keys()) == {
        "matrix_user_id",
        "role",
        "granted_at",
        "granted_by",
    }
    assert "password" not in UserRoleAssignment.__table__.columns
    assert "access_token" not in UserRoleAssignment.__table__.columns


def test_assignment_has_named_constraints_and_role_index() -> None:
    table = UserRoleAssignment.__table__
    assert isinstance(table, Table)
    constraint_names = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    }
    index_names = {index.name for index in table.indexes if isinstance(index, Index)}

    assert {
        "ck_user_role_assignments_granted_by",
        "ck_user_role_assignments_matrix_user_id",
        "ck_user_role_assignments_role",
    } <= constraint_names
    assert index_names == {"ix_user_role_assignments_role"}


def test_assignment_accepts_bootstrap_without_granting_actor() -> None:
    assignment = UserRoleAssignment(
        matrix_user_id="@admin:localhost",
        role=UserRole.platform_admin,
        granted_at=datetime(2026, 7, 22, 16, tzinfo=UTC),
        granted_by=None,
    )

    assert assignment.matrix_user_id == "@admin:localhost"
    assert assignment.role is UserRole.platform_admin
    assert assignment.granted_by is None
