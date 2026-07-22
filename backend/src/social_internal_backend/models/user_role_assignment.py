"""Papéis corporativos associados a identidades Matrix."""

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, Enum, Index, PrimaryKeyConstraint, String, func
from sqlalchemy.orm import Mapped, mapped_column

from social_internal_backend.database import Base
from social_internal_backend.models.enums import enum_values


class UserRole(StrEnum):
    """Papéis reconhecidos pelo serviço corporativo."""

    user = "user"
    group_admin = "group_admin"
    platform_admin = "platform_admin"


class UserRoleAssignment(Base):
    """Papel próprio sem duplicar a conta mantida pelo Synapse."""

    __tablename__ = "user_role_assignments"
    __table_args__ = (
        PrimaryKeyConstraint("matrix_user_id", name="pk_user_role_assignments"),
        CheckConstraint(
            "matrix_user_id ~ '^@[^[:space:]:]+:[^[:space:]]+$'",
            name="ck_user_role_assignments_matrix_user_id",
        ),
        CheckConstraint(
            "granted_by IS NULL OR granted_by ~ '^@[^[:space:]:]+:[^[:space:]]+$'",
            name="ck_user_role_assignments_granted_by",
        ),
        Index("ix_user_role_assignments_role", "role"),
    )

    matrix_user_id: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="ck_user_role_assignments_role",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            values_callable=enum_values,
            length=32,
        )
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    granted_by: Mapped[str | None] = mapped_column(String(255))
