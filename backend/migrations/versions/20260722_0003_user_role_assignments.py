"""Cria as atribuições de papéis corporativos.

Revision ID: 20260722_0003
Revises: 20260722_0002
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260722_0003"
down_revision: str | Sequence[str] | None = "20260722_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Cria uma associação de papel por identidade Matrix."""

    op.create_table(
        "user_role_assignments",
        sa.Column("matrix_user_id", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "user",
                "group_admin",
                "platform_admin",
                name="ck_user_role_assignments_role",
                native_enum=False,
                create_constraint=True,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("granted_by", sa.String(length=255), nullable=True),
        sa.CheckConstraint(
            "granted_by IS NULL OR granted_by ~ '^@[^[:space:]:]+:[^[:space:]]+$'",
            name="ck_user_role_assignments_granted_by",
        ),
        sa.CheckConstraint(
            "matrix_user_id ~ '^@[^[:space:]:]+:[^[:space:]]+$'",
            name="ck_user_role_assignments_matrix_user_id",
        ),
        sa.PrimaryKeyConstraint("matrix_user_id", name="pk_user_role_assignments"),
    )
    op.create_index(
        "ix_user_role_assignments_role",
        "user_role_assignments",
        ["role"],
        unique=False,
    )


def downgrade() -> None:
    """Remove integralmente as atribuições de papéis."""

    op.drop_index("ix_user_role_assignments_role", table_name="user_role_assignments")
    op.drop_table("user_role_assignments")
