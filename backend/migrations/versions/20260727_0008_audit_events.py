"""Cria a trilha administrativa sanitizada.

Revision ID: 20260727_0008
Revises: 20260727_0007
Create Date: 2026-07-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260727_0008"
down_revision: str | Sequence[str] | None = "20260727_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("target", sa.String(length=255), nullable=False),
        sa.Column("result", sa.String(length=16), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "action IN ('invitation_created', 'invitation_revoked', "
            "'activation_completed', 'provisioning_failed', 'account_locked', "
            "'account_unlocked', 'password_reset', 'account_deactivated')",
            name="ck_audit_events_action",
        ),
        sa.CheckConstraint(
            "result IN ('success', 'failure')",
            name="ck_audit_events_result",
        ),
        sa.CheckConstraint(
            "length(actor_user_id) BETWEEN 3 AND 255",
            name="ck_audit_actor",
        ),
        sa.CheckConstraint(
            "length(target) BETWEEN 1 AND 255",
            name="ck_audit_target",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_events"),
    )
    op.create_index(
        "ix_audit_events_occurred_at",
        "audit_events",
        ["occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_audit_events_target_occurred_at",
        "audit_events",
        ["target", "occurred_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_audit_events_target_occurred_at", table_name="audit_events")
    op.drop_index("ix_audit_events_occurred_at", table_name="audit_events")
    op.drop_table("audit_events")
