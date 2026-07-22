"""Cria a tabela de convites administrativos.

Revision ID: 20260722_0002
Revises: 20260722_0001
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260722_0002"
down_revision: str | Sequence[str] | None = "20260722_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Cria convites, restrições e índices operacionais."""

    op.create_table(
        "invitations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "user",
                "group_admin",
                name="ck_invitations_role",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "processing",
                "used",
                "revoked",
                "expired",
                name="ck_invitations_status",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_user_id", sa.String(length=255), nullable=True),
        sa.CheckConstraint(
            "expires_at > created_at",
            name="ck_invitations_expiration_after_creation",
        ),
        sa.CheckConstraint(
            "status <> 'revoked' OR revoked_at IS NOT NULL",
            name="ck_invitations_revoked_at",
        ),
        sa.CheckConstraint(
            "token_hash ~ '^[0-9a-f]{64}$'",
            name="ck_invitations_token_hash_sha256",
        ),
        sa.CheckConstraint(
            "status <> 'used' OR (used_at IS NOT NULL AND accepted_user_id IS NOT NULL)",
            name="ck_invitations_used_fields",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_invitations"),
        sa.UniqueConstraint("token_hash", name="uq_invitations_token_hash"),
    )
    op.create_index(
        "ix_invitations_created_by_created_at",
        "invitations",
        ["created_by", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_invitations_status_expires_at",
        "invitations",
        ["status", "expires_at"],
        unique=False,
    )


def downgrade() -> None:
    """Remove integralmente a tabela de convites."""

    op.drop_index("ix_invitations_status_expires_at", table_name="invitations")
    op.drop_index("ix_invitations_created_by_created_at", table_name="invitations")
    op.drop_table("invitations")
