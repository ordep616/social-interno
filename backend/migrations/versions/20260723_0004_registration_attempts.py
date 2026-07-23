"""Cria as tentativas duráveis da saga de cadastro.

Revision ID: 20260723_0004
Revises: 20260722_0003
Create Date: 2026-07-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260723_0004"
down_revision: str | Sequence[str] | None = "20260722_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ACTIVE_ATTEMPT_PREDICATE = "status IN ('processing', 'synapse_created', 'reconciliation_required')"


def upgrade() -> None:
    """Cria tentativas, restrições e índices de concorrência."""

    op.create_table(
        "registration_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("invitation_id", sa.Uuid(), nullable=False),
        sa.Column("matrix_user_id", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "user",
                "group_admin",
                name="ck_registration_attempts_role",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "processing",
                "synapse_created",
                "completed",
                "released",
                "reconciliation_required",
                name="ck_registration_attempts_status",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            server_default=sa.text("'processing'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_code", sa.String(length=64), nullable=True),
        sa.CheckConstraint(
            "(status = 'completed' AND completed_at IS NOT NULL) OR "
            "(status <> 'completed' AND completed_at IS NULL)",
            name="ck_registration_attempts_completed_at",
        ),
        sa.CheckConstraint(
            "completed_at IS NULL OR completed_at >= created_at",
            name="ck_registration_attempts_completed_after_creation",
        ),
        sa.CheckConstraint(
            "failure_code IS NULL OR failure_code ~ '^[a-z][a-z0-9_]{0,63}$'",
            name="ck_registration_attempts_failure_code",
        ),
        sa.CheckConstraint(
            "(status IN ('released', 'reconciliation_required') "
            "AND failure_code IS NOT NULL) OR "
            "(status IN ('processing', 'synapse_created', 'completed') "
            "AND failure_code IS NULL)",
            name="ck_registration_attempts_failure_state",
        ),
        sa.CheckConstraint(
            "matrix_user_id ~ '^@[^[:space:]:]+:[^[:space:]]+$'",
            name="ck_registration_attempts_matrix_user_id",
        ),
        sa.CheckConstraint(
            "updated_at >= created_at",
            name="ck_registration_attempts_updated_at",
        ),
        sa.ForeignKeyConstraint(
            ["invitation_id"],
            ["invitations.id"],
            name="fk_registration_attempts_invitation_id_invitations",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_registration_attempts"),
    )
    op.create_index(
        "ix_registration_attempts_status_updated_at",
        "registration_attempts",
        ["status", "updated_at"],
        unique=False,
    )
    op.create_index(
        "uq_registration_attempts_active_invitation_id",
        "registration_attempts",
        ["invitation_id"],
        unique=True,
        postgresql_where=sa.text(ACTIVE_ATTEMPT_PREDICATE),
    )
    op.create_index(
        "uq_registration_attempts_active_matrix_user_id",
        "registration_attempts",
        ["matrix_user_id"],
        unique=True,
        postgresql_where=sa.text(ACTIVE_ATTEMPT_PREDICATE),
    )


def downgrade() -> None:
    """Remove integralmente o estado operacional de cadastro."""

    op.drop_index(
        "uq_registration_attempts_active_matrix_user_id",
        table_name="registration_attempts",
        postgresql_where=sa.text(ACTIVE_ATTEMPT_PREDICATE),
    )
    op.drop_index(
        "uq_registration_attempts_active_invitation_id",
        table_name="registration_attempts",
        postgresql_where=sa.text(ACTIVE_ATTEMPT_PREDICATE),
    )
    op.drop_index(
        "ix_registration_attempts_status_updated_at",
        table_name="registration_attempts",
    )
    op.drop_table("registration_attempts")
