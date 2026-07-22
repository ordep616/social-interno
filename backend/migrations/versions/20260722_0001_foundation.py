"""Estabelece a fundação do banco próprio.

Revision ID: 20260722_0001
Revises:
Create Date: 2026-07-22
"""

from collections.abc import Sequence

revision: str = "20260722_0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Registra a revisão-base sem criar tabelas de negócio."""


def downgrade() -> None:
    """Remove apenas o marco da revisão-base."""
