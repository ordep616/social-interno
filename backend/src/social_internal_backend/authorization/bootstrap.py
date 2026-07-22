"""Inicialização local e única do primeiro administrador da plataforma."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy.orm import Session

from social_internal_backend.authorization.repository import UserRoleAssignmentRepository
from social_internal_backend.models import UserRole, UserRoleAssignment

Clock = Callable[[], datetime]


class UserRoleAssignmentRepositoryPort(Protocol):
    """Operações usadas pelo bootstrap administrativo."""

    def lock_for_bootstrap(self) -> None: ...

    def add(self, assignment: UserRoleAssignment) -> UserRoleAssignment: ...

    def get(self, matrix_user_id: str) -> UserRoleAssignment | None: ...

    def get_first_platform_admin(self) -> UserRoleAssignment | None: ...


class BootstrapAlreadyCompletedError(Exception):
    """Outro administrador já concluiu o bootstrap da instalação."""


@dataclass(frozen=True, slots=True)
class BootstrapResult:
    """Resultado sem credenciais do procedimento local."""

    assignment: UserRoleAssignment
    created: bool


def utc_now() -> datetime:
    """Fornece o instante atual em UTC."""

    return datetime.now(UTC)


def validate_matrix_user_id(matrix_user_id: str) -> str:
    """Aceita uma identidade Matrix completa sem tentar normalizá-la."""

    if len(matrix_user_id) > 255 or any(
        character.isspace() or not character.isprintable() for character in matrix_user_id
    ):
        raise ValueError("invalid Matrix user ID")
    if not matrix_user_id.startswith("@") or ":" not in matrix_user_id[1:]:
        raise ValueError("invalid Matrix user ID")

    localpart, server_name = matrix_user_id[1:].split(":", maxsplit=1)
    if not localpart or not server_name:
        raise ValueError("invalid Matrix user ID")
    return matrix_user_id


class PlatformAdminBootstrapService:
    """Cria exatamente o primeiro `platform_admin` por procedimento local."""

    def __init__(
        self,
        session: Session,
        *,
        repository: UserRoleAssignmentRepositoryPort | None = None,
        clock: Clock = utc_now,
    ) -> None:
        self._session = session
        self._repository = (
            repository if repository is not None else UserRoleAssignmentRepository(session)
        )
        self._clock = clock

    def bootstrap(self, matrix_user_id: str) -> BootstrapResult:
        """Atribui o papel inicial de forma serializada e idempotente."""

        validated_user_id = validate_matrix_user_id(matrix_user_id)
        try:
            self._repository.lock_for_bootstrap()
            assignment = self._repository.get(validated_user_id)
            if assignment is not None and assignment.role is UserRole.platform_admin:
                self._session.commit()
                return BootstrapResult(assignment=assignment, created=False)

            existing_admin = self._repository.get_first_platform_admin()
            if existing_admin is not None:
                raise BootstrapAlreadyCompletedError

            now = self._now()
            if assignment is None:
                assignment = UserRoleAssignment(
                    matrix_user_id=validated_user_id,
                    role=UserRole.platform_admin,
                    granted_at=now,
                    granted_by=None,
                )
                self._repository.add(assignment)
            else:
                assignment.role = UserRole.platform_admin
                assignment.granted_at = now
                assignment.granted_by = None

            self._session.commit()
            return BootstrapResult(assignment=assignment, created=True)
        except Exception:
            self._session.rollback()
            raise

    def _now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("clock must return a timezone-aware datetime")
        return now.astimezone(UTC)
