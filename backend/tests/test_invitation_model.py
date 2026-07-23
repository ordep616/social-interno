"""Contrato persistente do convite administrativo."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import CheckConstraint, Index, Table, UniqueConstraint

from social_internal_backend.models import Invitation, InvitationRole, InvitationStatus


def test_invitation_contains_only_approved_persistent_fields() -> None:
    assert set(Invitation.__table__.columns.keys()) == {
        "id",
        "token_hash",
        "role",
        "status",
        "created_by",
        "target_user_id",
        "created_at",
        "expires_at",
        "used_at",
        "revoked_at",
        "accepted_user_id",
    }
    assert "token" not in Invitation.__table__.columns
    assert "password" not in Invitation.__table__.columns


def test_invitation_roles_exclude_platform_admin() -> None:
    assert {role.value for role in InvitationRole} == {"user", "group_admin"}

    with pytest.raises(ValueError):
        InvitationRole("platform_admin")


def test_invitation_statuses_match_contract() -> None:
    assert {status.value for status in InvitationStatus} == {
        "pending",
        "processing",
        "used",
        "revoked",
        "expired",
        "conflicted",
    }


def test_invitation_has_named_constraints_and_indexes() -> None:
    table = Invitation.__table__
    assert isinstance(table, Table)
    constraint_names = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, (CheckConstraint, UniqueConstraint))
    }
    index_names = {index.name for index in table.indexes if isinstance(index, Index)}

    assert {
        "ck_invitations_expiration_after_creation",
        "ck_invitations_revoked_at",
        "ck_invitations_role",
        "ck_invitations_status",
        "ck_invitations_target_user_id_format",
        "ck_invitations_target_user_id_required",
        "ck_invitations_token_hash_sha256",
        "ck_invitations_used_fields",
        "uq_invitations_token_hash",
    } <= constraint_names
    assert index_names == {
        "ix_invitations_created_by_created_at",
        "ix_invitations_status_expires_at",
        "uq_invitations_active_target_user_id",
    }

    target_index = next(
        index for index in table.indexes if index.name == "uq_invitations_active_target_user_id"
    )
    assert target_index.unique
    target_predicate = str(target_index.dialect_options["postgresql"]["where"])
    assert "pending" in target_predicate
    assert "processing" in target_predicate
    assert "conflicted" not in target_predicate


def test_invitation_accepts_hash_but_not_original_token_field() -> None:
    now = datetime.now(UTC)
    invitation = Invitation(
        id=uuid4(),
        token_hash="a" * 64,
        role=InvitationRole.user,
        status=InvitationStatus.pending,
        created_by="@admin:localhost",
        target_user_id="@employee:localhost",
        created_at=now,
        expires_at=now + timedelta(hours=24),
    )

    assert invitation.token_hash == "a" * 64
    assert invitation.role is InvitationRole.user
    assert invitation.target_user_id == "@employee:localhost"
    assert not hasattr(invitation, "token")
