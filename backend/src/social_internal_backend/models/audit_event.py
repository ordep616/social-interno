"""Eventos administrativos mínimos e sanitizados."""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Enum, Index, PrimaryKeyConstraint, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from social_internal_backend.database import Base
from social_internal_backend.models.enums import enum_values


class AuditAction(StrEnum):
    invitation_created = "invitation_created"
    invitation_revoked = "invitation_revoked"
    activation_completed = "activation_completed"
    provisioning_failed = "provisioning_failed"
    account_locked = "account_locked"
    account_unlocked = "account_unlocked"
    password_reset = "password_reset"  # noqa: S105
    account_deactivated = "account_deactivated"


class AuditResult(StrEnum):
    success = "success"
    failure = "failure"


class AuditEvent(Base):
    """Registro sem corpo livre, token, senha ou credencial."""

    __tablename__ = "audit_events"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_audit_events"),
        CheckConstraint("length(actor_user_id) BETWEEN 3 AND 255", name="ck_audit_actor"),
        CheckConstraint("length(target) BETWEEN 1 AND 255", name="ck_audit_target"),
        Index("ix_audit_events_occurred_at", "occurred_at"),
        Index("ix_audit_events_target_occurred_at", "target", "occurred_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, default=uuid4)
    actor_user_id: Mapped[str] = mapped_column(String(255))
    action: Mapped[AuditAction] = mapped_column(
        Enum(
            AuditAction,
            name="ck_audit_events_action",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=enum_values,
            length=32,
        )
    )
    target: Mapped[str] = mapped_column(String(255))
    result: Mapped[AuditResult] = mapped_column(
        Enum(
            AuditResult,
            name="ck_audit_events_result",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=enum_values,
            length=16,
        )
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
