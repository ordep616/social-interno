"""Persistência de convites administrativos."""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    Index,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from social_internal_backend.database import Base
from social_internal_backend.models.enums import enum_values


class InvitationRole(StrEnum):
    """Papéis que podem ser concedidos diretamente por convite."""

    user = "user"
    group_admin = "group_admin"


class InvitationStatus(StrEnum):
    """Estados persistidos do ciclo de vida do convite."""

    pending = "pending"
    processing = "processing"
    used = "used"
    revoked = "revoked"
    expired = "expired"


class Invitation(Base):
    """Convite de uso único sem armazenamento do token original."""

    __tablename__ = "invitations"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_invitations"),
        UniqueConstraint("token_hash", name="uq_invitations_token_hash"),
        CheckConstraint(
            "token_hash ~ '^[0-9a-f]{64}$'",
            name="ck_invitations_token_hash_sha256",
        ),
        CheckConstraint(
            "expires_at > created_at",
            name="ck_invitations_expiration_after_creation",
        ),
        CheckConstraint(
            "status <> 'used' OR (used_at IS NOT NULL AND accepted_user_id IS NOT NULL)",
            name="ck_invitations_used_fields",
        ),
        CheckConstraint(
            "status <> 'revoked' OR revoked_at IS NOT NULL",
            name="ck_invitations_revoked_at",
        ),
        Index("ix_invitations_status_expires_at", "status", "expires_at"),
        Index("ix_invitations_created_by_created_at", "created_by", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, default=uuid4)
    token_hash: Mapped[str] = mapped_column(String(64))
    role: Mapped[InvitationRole] = mapped_column(
        Enum(
            InvitationRole,
            name="ck_invitations_role",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=enum_values,
            length=32,
        )
    )
    status: Mapped[InvitationStatus] = mapped_column(
        Enum(
            InvitationStatus,
            name="ck_invitations_status",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=enum_values,
            length=32,
        ),
        default=InvitationStatus.pending,
        server_default=InvitationStatus.pending.value,
    )
    created_by: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accepted_user_id: Mapped[str | None] = mapped_column(String(255))
