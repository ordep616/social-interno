"""Adiciona a identidade previamente definida aos convites.

Revision ID: 20260723_0005
Revises: 20260723_0004
Create Date: 2026-07-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260723_0005"
down_revision: str | Sequence[str] | None = "20260723_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ACTIVE_INVITATION_TARGET_PREDICATE = "status IN ('pending', 'processing')"
CURRENT_INVITATION_STATUSES = "status IN ('pending', 'processing', 'used', 'revoked', 'expired')"
TARGET_IDENTITY_INVITATION_STATUSES = (
    "status IN ('pending', 'processing', 'used', 'revoked', 'expired', 'conflicted')"
)


def upgrade() -> None:
    """Migra convites legados e exige identidade nos estados não históricos."""

    op.add_column(
        "invitations",
        sa.Column("target_user_id", sa.String(length=255), nullable=True),
    )

    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM invitations
                    WHERE status = 'processing'
                ) THEN
                    RAISE EXCEPTION
                        'invitation identity migration blocked by processing records';
                END IF;
            END
            $$;
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE invitations
            SET target_user_id = accepted_user_id
            WHERE status = 'used'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE invitations
            SET status = 'revoked',
                revoked_at = COALESCE(revoked_at, CURRENT_TIMESTAMP)
            WHERE status = 'pending'
            """
        )
    )

    op.drop_constraint("ck_invitations_status", "invitations", type_="check")
    op.create_check_constraint(
        "ck_invitations_status",
        "invitations",
        TARGET_IDENTITY_INVITATION_STATUSES,
    )
    op.create_check_constraint(
        "ck_invitations_target_user_id_required",
        "invitations",
        "status IN ('revoked', 'expired') OR target_user_id IS NOT NULL",
    )
    op.create_check_constraint(
        "ck_invitations_target_user_id_format",
        "invitations",
        "target_user_id IS NULL OR target_user_id ~ '^@[^[:space:]:]+:[^[:space:]]+$'",
    )
    op.create_index(
        "uq_invitations_active_target_user_id",
        "invitations",
        ["target_user_id"],
        unique=True,
        postgresql_where=sa.text(ACTIVE_INVITATION_TARGET_PREDICATE),
    )


def downgrade() -> None:
    """Restaura o contrato anterior sem deixar estados incompatíveis."""

    op.drop_index(
        "uq_invitations_active_target_user_id",
        table_name="invitations",
        postgresql_where=sa.text(ACTIVE_INVITATION_TARGET_PREDICATE),
    )
    op.drop_constraint(
        "ck_invitations_target_user_id_format",
        "invitations",
        type_="check",
    )
    op.drop_constraint(
        "ck_invitations_target_user_id_required",
        "invitations",
        type_="check",
    )
    op.execute(
        sa.text(
            """
            UPDATE invitations
            SET status = 'revoked',
                revoked_at = COALESCE(revoked_at, CURRENT_TIMESTAMP)
            WHERE status = 'conflicted'
            """
        )
    )
    op.drop_constraint("ck_invitations_status", "invitations", type_="check")
    op.create_check_constraint(
        "ck_invitations_status",
        "invitations",
        CURRENT_INVITATION_STATUSES,
    )
    op.drop_column("invitations", "target_user_id")
