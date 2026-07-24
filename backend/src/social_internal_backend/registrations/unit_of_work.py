"""Limites transacionais locais da saga durável de cadastro."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from social_internal_backend.authorization.repository import (
    UserRoleAssignmentRepository,
)
from social_internal_backend.invitations.repository import InvitationRepository
from social_internal_backend.models import (
    Invitation,
    InvitationRole,
    InvitationStatus,
    RegistrationAttempt,
    RegistrationAttemptStatus,
    UserRole,
    UserRoleAssignment,
)
from social_internal_backend.registrations.repository import (
    RegistrationAttemptRepository,
)

TOKEN_HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
FAILURE_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
MAX_PROVISIONING_DEVICE_ID_LENGTH = 255


class InvitationRepositoryPort(Protocol):
    """Operações de convite usadas nos limites transacionais."""

    def get(self, invitation_id: UUID) -> Invitation | None: ...

    def claim_pending(self, token_hash: str, now: datetime) -> Invitation | None: ...

    def complete_processing(
        self,
        invitation_id: UUID,
        accepted_user_id: str,
        now: datetime,
    ) -> Invitation | None: ...

    def release_processing(
        self,
        invitation_id: UUID,
        now: datetime,
    ) -> Invitation | None: ...


class RegistrationAttemptRepositoryPort(Protocol):
    """Operações de tentativa usadas nos limites transacionais."""

    def add(self, attempt: RegistrationAttempt) -> RegistrationAttempt: ...

    def get(self, attempt_id: UUID) -> RegistrationAttempt | None: ...

    def mark_synapse_created(
        self,
        attempt_id: UUID,
        *,
        provisioning_device_id: str,
        now: datetime,
    ) -> RegistrationAttempt | None: ...

    def mark_provisioning_session_revoked(
        self,
        attempt_id: UUID,
        *,
        provisioning_device_id: str,
        now: datetime,
    ) -> RegistrationAttempt | None: ...

    def mark_completed(
        self,
        attempt_id: UUID,
        now: datetime,
    ) -> RegistrationAttempt | None: ...

    def mark_released(
        self,
        attempt_id: UUID,
        *,
        failure_code: str,
        now: datetime,
    ) -> RegistrationAttempt | None: ...

    def mark_reconciliation_required(
        self,
        attempt_id: UUID,
        *,
        failure_code: str,
        now: datetime,
    ) -> RegistrationAttempt | None: ...


class UserRoleAssignmentRepositoryPort(Protocol):
    """Operações de papel usadas na finalização local."""

    def add(self, assignment: UserRoleAssignment) -> UserRoleAssignment: ...


class RegistrationTransactionConflictError(Exception):
    """Uma transação local não satisfez suas pré-condições."""


class RegistrationReservationConflictError(RegistrationTransactionConflictError):
    """Convite e tentativa não puderam ser reservados juntos."""


class RegistrationCheckpointConflictError(RegistrationTransactionConflictError):
    """Um checkpoint durável não pôde ser registrado."""


class RegistrationReleaseConflictError(RegistrationTransactionConflictError):
    """Convite e tentativa não puderam ser liberados juntos."""


class RegistrationFinalizationConflictError(RegistrationTransactionConflictError):
    """Papel, convite e tentativa não puderam ser concluídos juntos."""


@dataclass(frozen=True, slots=True)
class RegistrationReservation:
    """Convite reservado e tentativa criados no mesmo commit."""

    invitation: Invitation
    attempt: RegistrationAttempt


@dataclass(frozen=True, slots=True)
class RegistrationRelease:
    """Convite liberado e tentativa encerrada no mesmo commit."""

    invitation: Invitation
    attempt: RegistrationAttempt


@dataclass(frozen=True, slots=True)
class RegistrationFinalization:
    """Papel, convite e tentativa concluídos no mesmo commit."""

    invitation: Invitation
    attempt: RegistrationAttempt
    role_assignment: UserRoleAssignment


INVITATION_ROLE_TO_USER_ROLE = {
    InvitationRole.user: UserRole.user,
    InvitationRole.group_admin: UserRole.group_admin,
}


class RegistrationUnitOfWork:
    """Coordena somente transações PostgreSQL curtas, sem operações externas."""

    def __init__(
        self,
        session: Session,
        *,
        invitation_repository: InvitationRepositoryPort | None = None,
        attempt_repository: RegistrationAttemptRepositoryPort | None = None,
        role_repository: UserRoleAssignmentRepositoryPort | None = None,
    ) -> None:
        self._session = session
        self._invitations = (
            invitation_repository
            if invitation_repository is not None
            else InvitationRepository(session)
        )
        self._attempts = (
            attempt_repository
            if attempt_repository is not None
            else RegistrationAttemptRepository(session)
        )
        self._roles = (
            role_repository
            if role_repository is not None
            else UserRoleAssignmentRepository(session)
        )

    def reserve(
        self,
        *,
        token_hash: str,
        now: datetime,
    ) -> RegistrationReservation:
        """Reserva o convite e deriva a tentativa da identidade autorizada."""

        self._validate_token_hash(token_hash)
        self._validate_timestamp(now)
        try:
            invitation = self._invitations.claim_pending(token_hash, now)
            if (
                invitation is None
                or invitation.status is not InvitationStatus.processing
                or invitation.target_user_id is None
            ):
                raise RegistrationReservationConflictError

            attempt = RegistrationAttempt(
                invitation_id=invitation.id,
                matrix_user_id=invitation.target_user_id,
                role=invitation.role,
                status=RegistrationAttemptStatus.processing,
                created_at=now,
                updated_at=now,
            )
            self._attempts.add(attempt)
            self._session.commit()
        except RegistrationReservationConflictError:
            self._session.rollback()
            raise
        except IntegrityError:
            self._session.rollback()
            raise RegistrationReservationConflictError from None
        except Exception:
            self._session.rollback()
            raise

        return RegistrationReservation(invitation=invitation, attempt=attempt)

    def record_synapse_created(
        self,
        *,
        attempt_id: UUID,
        provisioning_device_id: str,
        now: datetime,
    ) -> RegistrationAttempt:
        """Registra criação validada sem conservar a sessão ou a senha."""

        self._validate_device_id(provisioning_device_id)
        self._validate_timestamp(now)
        try:
            attempt = self._attempts.mark_synapse_created(
                attempt_id,
                provisioning_device_id=provisioning_device_id,
                now=now,
            )
            if attempt is None:
                raise RegistrationCheckpointConflictError
            self._session.commit()
        except RegistrationCheckpointConflictError:
            self._session.rollback()
            raise
        except IntegrityError:
            self._session.rollback()
            raise RegistrationCheckpointConflictError from None
        except Exception:
            self._session.rollback()
            raise
        return attempt

    def record_reconciliation_required(
        self,
        *,
        attempt_id: UUID,
        failure_code: str,
        now: datetime,
    ) -> RegistrationAttempt:
        """Persiste resultado ambíguo sem liberar o convite."""

        self._validate_failure_code(failure_code)
        self._validate_timestamp(now)
        try:
            attempt = self._attempts.mark_reconciliation_required(
                attempt_id,
                failure_code=failure_code,
                now=now,
            )
            if attempt is None:
                raise RegistrationCheckpointConflictError
            self._session.commit()
        except RegistrationCheckpointConflictError:
            self._session.rollback()
            raise
        except IntegrityError:
            self._session.rollback()
            raise RegistrationCheckpointConflictError from None
        except Exception:
            self._session.rollback()
            raise
        return attempt

    def record_provisioning_session_revoked(
        self,
        *,
        attempt_id: UUID,
        provisioning_device_id: str,
        now: datetime,
    ) -> RegistrationAttempt:
        """Registra revogação confirmada e recupera reconciliação atomicamente."""

        self._validate_device_id(provisioning_device_id)
        self._validate_timestamp(now)
        try:
            attempt = self._attempts.mark_provisioning_session_revoked(
                attempt_id,
                provisioning_device_id=provisioning_device_id,
                now=now,
            )
            if attempt is None:
                raise RegistrationCheckpointConflictError
            self._session.commit()
        except RegistrationCheckpointConflictError:
            self._session.rollback()
            raise
        except IntegrityError:
            self._session.rollback()
            raise RegistrationCheckpointConflictError from None
        except Exception:
            self._session.rollback()
            raise
        return attempt

    def release(
        self,
        *,
        attempt_id: UUID,
        failure_code: str,
        now: datetime,
    ) -> RegistrationRelease:
        """Libera somente uma falha classificada pelo chamador como segura."""

        self._validate_failure_code(failure_code)
        self._validate_timestamp(now)
        try:
            attempt = self._attempts.get(attempt_id)
            if attempt is None or attempt.status is not RegistrationAttemptStatus.processing:
                raise RegistrationReleaseConflictError

            invitation = self._invitations.get(attempt.invitation_id)
            if not self._matches_processing_invitation(invitation, attempt):
                raise RegistrationReleaseConflictError

            released_attempt = self._attempts.mark_released(
                attempt.id,
                failure_code=failure_code,
                now=now,
            )
            released_invitation = self._invitations.release_processing(
                attempt.invitation_id,
                now,
            )
            if released_attempt is None or released_invitation is None:
                raise RegistrationReleaseConflictError
            self._session.commit()
        except RegistrationReleaseConflictError:
            self._session.rollback()
            raise
        except IntegrityError:
            self._session.rollback()
            raise RegistrationReleaseConflictError from None
        except Exception:
            self._session.rollback()
            raise

        return RegistrationRelease(
            invitation=released_invitation,
            attempt=released_attempt,
        )

    def finalize(
        self,
        *,
        attempt_id: UUID,
        now: datetime,
    ) -> RegistrationFinalization:
        """Conclui somente depois da evidência durável de revogação."""

        self._validate_timestamp(now)
        try:
            attempt = self._attempts.get(attempt_id)
            if (
                attempt is None
                or attempt.status is not RegistrationAttemptStatus.synapse_created
                or not attempt.provisioning_device_id
                or attempt.provisioning_session_revoked_at is None
                or attempt.provisioning_session_revoked_at > now
            ):
                raise RegistrationFinalizationConflictError

            invitation = self._invitations.get(attempt.invitation_id)
            if not self._matches_processing_invitation(invitation, attempt):
                raise RegistrationFinalizationConflictError
            if invitation is None or invitation.target_user_id is None:
                raise RegistrationFinalizationConflictError

            completed_invitation = self._invitations.complete_processing(
                invitation.id,
                invitation.target_user_id,
                now,
            )
            completed_attempt = self._attempts.mark_completed(attempt.id, now)
            if completed_invitation is None or completed_attempt is None:
                raise RegistrationFinalizationConflictError

            role_assignment = UserRoleAssignment(
                matrix_user_id=invitation.target_user_id,
                role=INVITATION_ROLE_TO_USER_ROLE[invitation.role],
                granted_at=now,
                granted_by=invitation.created_by,
            )
            self._roles.add(role_assignment)
            self._session.commit()
        except RegistrationFinalizationConflictError:
            self._session.rollback()
            raise
        except IntegrityError, KeyError:
            self._session.rollback()
            raise RegistrationFinalizationConflictError from None
        except Exception:
            self._session.rollback()
            raise

        return RegistrationFinalization(
            invitation=completed_invitation,
            attempt=completed_attempt,
            role_assignment=role_assignment,
        )

    @staticmethod
    def _matches_processing_invitation(
        invitation: Invitation | None,
        attempt: RegistrationAttempt,
    ) -> bool:
        return (
            invitation is not None
            and invitation.status is InvitationStatus.processing
            and invitation.target_user_id is not None
            and invitation.target_user_id == attempt.matrix_user_id
            and invitation.role is attempt.role
        )

    @staticmethod
    def _validate_token_hash(token_hash: str) -> None:
        if TOKEN_HASH_PATTERN.fullmatch(token_hash) is None:
            raise ValueError("token_hash must be a lowercase SHA-256 digest")

    @staticmethod
    def _validate_failure_code(failure_code: str) -> None:
        if FAILURE_CODE_PATTERN.fullmatch(failure_code) is None:
            raise ValueError("failure_code has an invalid format")

    @staticmethod
    def _validate_device_id(provisioning_device_id: str) -> None:
        if not 1 <= len(provisioning_device_id) <= MAX_PROVISIONING_DEVICE_ID_LENGTH:
            raise ValueError("provisioning_device_id has an invalid length")

    @staticmethod
    def _validate_timestamp(now: datetime) -> None:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now must be timezone-aware")
