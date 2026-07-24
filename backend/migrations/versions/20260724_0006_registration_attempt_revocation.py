"""Adiciona evidência durável da revogação de provisionamento.

Revision ID: 20260724_0006
Revises: 20260723_0005
Create Date: 2026-07-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260724_0006"
down_revision: str | Sequence[str] | None = "20260723_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Adiciona a evidência e impede conclusão sem revogação confirmada."""

    op.add_column(
        "registration_attempts",
        sa.Column("provisioning_device_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "registration_attempts",
        sa.Column(
            "provisioning_session_revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM registration_attempts
                    WHERE status IN ('synapse_created', 'completed')
                ) THEN
                    RAISE EXCEPTION
                        'migration blocked: registration attempts lack provisioning evidence';
                END IF;
            END
            $$;
            """
        )
    )

    op.create_check_constraint(
        "ck_registration_attempts_provisioning_device_required",
        "registration_attempts",
        "status NOT IN ('synapse_created', 'completed') OR provisioning_device_id IS NOT NULL",
    )
    op.create_check_constraint(
        "ck_registration_attempts_provisioning_revocation_required",
        "registration_attempts",
        "status <> 'completed' OR provisioning_session_revoked_at IS NOT NULL",
    )
    op.create_check_constraint(
        "ck_registration_attempts_provisioning_revocation_metadata",
        "registration_attempts",
        "provisioning_session_revoked_at IS NULL OR "
        "(provisioning_device_id IS NOT NULL "
        "AND status IN ('synapse_created', 'completed') "
        "AND provisioning_session_revoked_at >= created_at)",
    )
    op.create_check_constraint(
        "ck_registration_attempts_unprovisioned_states",
        "registration_attempts",
        "status NOT IN ('processing', 'released') OR "
        "(provisioning_device_id IS NULL "
        "AND provisioning_session_revoked_at IS NULL)",
    )


def downgrade() -> None:
    """Remove as invariantes e os campos de evidência de provisionamento."""

    op.drop_constraint(
        "ck_registration_attempts_unprovisioned_states",
        "registration_attempts",
        type_="check",
    )
    op.drop_constraint(
        "ck_registration_attempts_provisioning_revocation_metadata",
        "registration_attempts",
        type_="check",
    )
    op.drop_constraint(
        "ck_registration_attempts_provisioning_revocation_required",
        "registration_attempts",
        type_="check",
    )
    op.drop_constraint(
        "ck_registration_attempts_provisioning_device_required",
        "registration_attempts",
        type_="check",
    )
    op.drop_column(
        "registration_attempts",
        "provisioning_session_revoked_at",
    )
    op.drop_column("registration_attempts", "provisioning_device_id")
