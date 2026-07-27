"""Contadores persistentes dos fluxos públicos de ativação."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKeyConstraint,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from social_internal_backend.database import Base
from social_internal_backend.models.enums import enum_values


class ActivationRateLimitKind(StrEnum):
    """Operações públicas que não podem compartilhar o mesmo contador."""

    activation_validation = "activation_validation"
    registration = "registration"


class ActivationRateLimit(Base):
    """Janela limitada sem token aberto, senha ou endereço de origem."""

    __tablename__ = "activation_rate_limits"
    __table_args__ = (
        PrimaryKeyConstraint(
            "counter_kind",
            "invitation_token_hash",
            "window_started_at",
            name="pk_activation_rate_limits",
        ),
        ForeignKeyConstraint(
            ["invitation_token_hash"],
            ["invitations.token_hash"],
            name="fk_activation_rate_limits_invitation_token_hash_invitations",
        ),
        CheckConstraint(
            "invitation_token_hash ~ '^[0-9a-f]{64}$'",
            name="ck_activation_rate_limits_token_hash_sha256",
        ),
        CheckConstraint(
            "attempt_count >= 1",
            name="ck_activation_rate_limits_attempt_count_positive",
        ),
        CheckConstraint(
            "window_ends_at = window_started_at + INTERVAL '15 minutes'",
            name="ck_activation_rate_limits_window_duration",
        ),
        CheckConstraint(
            "expires_at = window_ends_at + INTERVAL '1 hour'",
            name="ck_activation_rate_limits_retention",
        ),
        Index("ix_activation_rate_limits_expires_at", "expires_at"),
    )

    counter_kind: Mapped[ActivationRateLimitKind] = mapped_column(
        Enum(
            ActivationRateLimitKind,
            name="ck_activation_rate_limits_counter_kind",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=enum_values,
            length=32,
        )
    )
    invitation_token_hash: Mapped[str] = mapped_column(String(64))
    window_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    window_ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    attempt_count: Mapped[int] = mapped_column(Integer)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
