"""Tentativas duráveis da saga de cadastro."""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKeyConstraint,
    Index,
    PrimaryKeyConstraint,
    String,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from social_internal_backend.database import Base
from social_internal_backend.models.enums import enum_values
from social_internal_backend.models.invitation import InvitationRole

ACTIVE_REGISTRATION_ATTEMPT_PREDICATE = (
    "status IN ('processing', 'synapse_created', 'reconciliation_required')"
)


class RegistrationAttemptStatus(StrEnum):
    """Estados operacionais que permitem retomar ou reconciliar o cadastro."""

    processing = "processing"
    synapse_created = "synapse_created"
    completed = "completed"
    released = "released"
    reconciliation_required = "reconciliation_required"


class RegistrationAttempt(Base):
    """Estado operacional sem token, senha ou credencial administrativa."""

    __tablename__ = "registration_attempts"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_registration_attempts"),
        ForeignKeyConstraint(
            ["invitation_id"],
            ["invitations.id"],
            name="fk_registration_attempts_invitation_id_invitations",
        ),
        CheckConstraint(
            "matrix_user_id ~ '^@[^[:space:]:]+:[^[:space:]]+$'",
            name="ck_registration_attempts_matrix_user_id",
        ),
        CheckConstraint(
            "updated_at >= created_at",
            name="ck_registration_attempts_updated_at",
        ),
        CheckConstraint(
            "(status = 'completed' AND completed_at IS NOT NULL) OR "
            "(status <> 'completed' AND completed_at IS NULL)",
            name="ck_registration_attempts_completed_at",
        ),
        CheckConstraint(
            "completed_at IS NULL OR completed_at >= created_at",
            name="ck_registration_attempts_completed_after_creation",
        ),
        CheckConstraint(
            "(status IN ('released', 'reconciliation_required') "
            "AND failure_code IS NOT NULL) OR "
            "(status IN ('processing', 'synapse_created', 'completed') "
            "AND failure_code IS NULL)",
            name="ck_registration_attempts_failure_state",
        ),
        CheckConstraint(
            "failure_code IS NULL OR failure_code ~ '^[a-z][a-z0-9_]{0,63}$'",
            name="ck_registration_attempts_failure_code",
        ),
        Index(
            "uq_registration_attempts_active_invitation_id",
            "invitation_id",
            unique=True,
            postgresql_where=text(ACTIVE_REGISTRATION_ATTEMPT_PREDICATE),
        ),
        Index(
            "uq_registration_attempts_active_matrix_user_id",
            "matrix_user_id",
            unique=True,
            postgresql_where=text(ACTIVE_REGISTRATION_ATTEMPT_PREDICATE),
        ),
        Index(
            "ix_registration_attempts_status_updated_at",
            "status",
            "updated_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, default=uuid4)
    invitation_id: Mapped[UUID] = mapped_column(Uuid)
    matrix_user_id: Mapped[str] = mapped_column(String(255))
    role: Mapped[InvitationRole] = mapped_column(
        Enum(
            InvitationRole,
            name="ck_registration_attempts_role",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=enum_values,
            length=32,
        )
    )
    status: Mapped[RegistrationAttemptStatus] = mapped_column(
        Enum(
            RegistrationAttemptStatus,
            name="ck_registration_attempts_status",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=enum_values,
            length=32,
        ),
        default=RegistrationAttemptStatus.processing,
        server_default=RegistrationAttemptStatus.processing.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        onupdate=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_code: Mapped[str | None] = mapped_column(String(64))
