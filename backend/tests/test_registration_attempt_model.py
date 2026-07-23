"""Contrato persistente das tentativas de cadastro."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import CheckConstraint, Enum, ForeignKeyConstraint, Index, Table

from social_internal_backend.models import (
    InvitationRole,
    RegistrationAttempt,
    RegistrationAttemptStatus,
)


def test_attempt_contains_only_approved_operational_fields() -> None:
    assert set(RegistrationAttempt.__table__.columns.keys()) == {
        "id",
        "invitation_id",
        "matrix_user_id",
        "role",
        "status",
        "created_at",
        "updated_at",
        "completed_at",
        "failure_code",
    }
    for forbidden_field in {
        "token",
        "token_hash",
        "password",
        "access_token",
        "admin_access_token",
        "synapse_response",
    }:
        assert forbidden_field not in RegistrationAttempt.__table__.columns


def test_attempt_statuses_match_decision() -> None:
    assert {status.value for status in RegistrationAttemptStatus} == {
        "processing",
        "synapse_created",
        "completed",
        "released",
        "reconciliation_required",
    }

    with pytest.raises(ValueError):
        RegistrationAttemptStatus("unknown")


def test_attempt_role_cannot_grant_platform_admin() -> None:
    role_type = RegistrationAttempt.__table__.columns.role.type
    assert isinstance(role_type, Enum)

    assert set(role_type.enums) == {"user", "group_admin"}
    assert "platform_admin" not in role_type.enums


def test_attempt_has_named_constraints_and_indexes() -> None:
    table = RegistrationAttempt.__table__
    assert isinstance(table, Table)
    constraint_names = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, (CheckConstraint, ForeignKeyConstraint))
    }
    indexes = {str(index.name): index for index in table.indexes if isinstance(index, Index)}

    assert {
        "ck_registration_attempts_completed_after_creation",
        "ck_registration_attempts_completed_at",
        "ck_registration_attempts_failure_code",
        "ck_registration_attempts_failure_state",
        "ck_registration_attempts_matrix_user_id",
        "ck_registration_attempts_role",
        "ck_registration_attempts_status",
        "ck_registration_attempts_updated_at",
        "fk_registration_attempts_invitation_id_invitations",
    } <= constraint_names
    assert set(indexes) == {
        "ix_registration_attempts_status_updated_at",
        "uq_registration_attempts_active_invitation_id",
        "uq_registration_attempts_active_matrix_user_id",
    }
    assert not indexes["ix_registration_attempts_status_updated_at"].unique
    for index_name in {
        "uq_registration_attempts_active_invitation_id",
        "uq_registration_attempts_active_matrix_user_id",
    }:
        index = indexes[index_name]
        assert index.unique
        predicate = str(index.dialect_options["postgresql"]["where"])
        assert "processing" in predicate
        assert "synapse_created" in predicate
        assert "reconciliation_required" in predicate
        assert "released" not in predicate
        assert "completed" not in predicate


def test_attempt_accepts_only_operational_metadata() -> None:
    now = datetime(2026, 7, 23, 12, tzinfo=UTC)
    attempt = RegistrationAttempt(
        id=uuid4(),
        invitation_id=uuid4(),
        matrix_user_id="@alice:localhost",
        role=InvitationRole.user,
        status=RegistrationAttemptStatus.processing,
        created_at=now,
        updated_at=now,
    )

    assert attempt.matrix_user_id == "@alice:localhost"
    assert attempt.role is InvitationRole.user
    assert attempt.status is RegistrationAttemptStatus.processing
    assert not hasattr(attempt, "password")
