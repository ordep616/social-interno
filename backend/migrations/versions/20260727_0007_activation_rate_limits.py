"""Adiciona contadores persistentes dos fluxos de ativação.

Revision ID: 20260727_0007
Revises: 20260724_0006
Create Date: 2026-07-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260727_0007"
down_revision: str | Sequence[str] | None = "20260724_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Cria contadores separados, limitados e vinculados a convites existentes."""

    op.create_table(
        "activation_rate_limits",
        sa.Column("counter_kind", sa.String(length=32), nullable=False),
        sa.Column("invitation_token_hash", sa.String(length=64), nullable=False),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "counter_kind IN ('activation_validation', 'registration')",
            name="ck_activation_rate_limits_counter_kind",
        ),
        sa.CheckConstraint(
            "invitation_token_hash ~ '^[0-9a-f]{64}$'",
            name="ck_activation_rate_limits_token_hash_sha256",
        ),
        sa.CheckConstraint(
            "attempt_count >= 1",
            name="ck_activation_rate_limits_attempt_count_positive",
        ),
        sa.CheckConstraint(
            "window_ends_at = window_started_at + INTERVAL '15 minutes'",
            name="ck_activation_rate_limits_window_duration",
        ),
        sa.CheckConstraint(
            "expires_at = window_ends_at + INTERVAL '1 hour'",
            name="ck_activation_rate_limits_retention",
        ),
        sa.ForeignKeyConstraint(
            ["invitation_token_hash"],
            ["invitations.token_hash"],
            name="fk_activation_rate_limits_invitation_token_hash_invitations",
        ),
        sa.PrimaryKeyConstraint(
            "counter_kind",
            "invitation_token_hash",
            "window_started_at",
            name="pk_activation_rate_limits",
        ),
    )
    op.create_index(
        "ix_activation_rate_limits_expires_at",
        "activation_rate_limits",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    """Remove integralmente o armazenamento operacional do limitador."""

    op.drop_index(
        "ix_activation_rate_limits_expires_at",
        table_name="activation_rate_limits",
    )
    op.drop_table("activation_rate_limits")
