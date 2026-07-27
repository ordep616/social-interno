"""Pré-validação somente leitura de identidades previamente autorizadas."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from social_internal_backend.invitations import InvitationRepository
from social_internal_backend.invitations.tokens import hash_invitation_token
from social_internal_backend.matrix import (
    build_local_matrix_user_id,
    validate_local_username,
    validate_matrix_user_id,
)
from social_internal_backend.models import (
    ActivationRateLimitKind,
    Invitation,
    InvitationRole,
    InvitationStatus,
)
from social_internal_backend.rate_limits import (
    ActivationRateLimitDecision,
    ActivationRateLimitRepository,
)
from social_internal_backend.registrations import RegistrationAttemptRepository
from social_internal_backend.synapse import SynapseUserNotFoundError

Clock = Callable[[], datetime]


class InvitationLookupPort(Protocol):
    """Consulta local mínima da pré-validação."""

    def get_by_token_hash(self, token_hash: str) -> Invitation | None: ...


class RegistrationAttemptLookupPort(Protocol):
    """Consulta tentativas que tornam a ativação ambígua."""

    def get_active_by_invitation(self, invitation_id: UUID) -> object | None: ...


class ActivationRateLimitPort(Protocol):
    """Consome somente contadores de convites previamente conhecidos."""

    def consume_existing_invitation(
        self,
        *,
        counter_kind: ActivationRateLimitKind,
        invitation_token_hash: str,
        now: datetime,
    ) -> ActivationRateLimitDecision | None: ...


class SynapseUserLookupPort(Protocol):
    """Confirma a ausência da identidade no homeserver."""

    def get_user(self, user_id: str) -> object: ...


class ActivationValidationNotFoundError(Exception):
    """O segredo não corresponde a um convite conhecido."""


class ActivationValidationUnavailableError(Exception):
    """O convite existe, mas terminou ou foi revogado."""


class ActivationValidationConflictError(Exception):
    """O convite, a tentativa ou a identidade não pode ser ativada."""


class ActivationValidationRateLimitedError(Exception):
    """O contador local recusou nova pré-validação na janela."""

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__("activation validation rate limit exceeded")
        self.retry_after_seconds = retry_after_seconds


class ActivationValidationStorageUnavailableError(Exception):
    """O PostgreSQL próprio não permitiu falhar com segurança."""


@dataclass(frozen=True, slots=True)
class ActivationValidationResult:
    """Metadados públicos derivados somente do convite persistido."""

    target_user_id: str
    username: str
    role: InvitationRole
    expires_at: datetime


def utc_now() -> datetime:
    """Fornece um instante UTC consciente de fuso."""

    return datetime.now(UTC)


class ActivationValidationService:
    """Valida estado, limite e disponibilidade sem reservar o convite."""

    def __init__(
        self,
        session: Session,
        *,
        identity_provider: SynapseUserLookupPort,
        matrix_server_name: str,
        invitation_repository: InvitationLookupPort | None = None,
        attempt_repository: RegistrationAttemptLookupPort | None = None,
        rate_limit_repository: ActivationRateLimitPort | None = None,
        clock: Clock = utc_now,
    ) -> None:
        self._session = session
        self._identity_provider = identity_provider
        self._matrix_server_name = matrix_server_name
        self._invitation_repository = (
            invitation_repository
            if invitation_repository is not None
            else InvitationRepository(session)
        )
        self._attempt_repository = (
            attempt_repository
            if attempt_repository is not None
            else RegistrationAttemptRepository(session)
        )
        self._rate_limit_repository = (
            rate_limit_repository
            if rate_limit_repository is not None
            else ActivationRateLimitRepository(session)
        )
        self._clock = clock

    def validate(self, invitation_token: str) -> ActivationValidationResult:
        """Pré-valida um segredo sem persistir o valor ou alterar o convite."""

        token_hash = hash_invitation_token(invitation_token)
        now = self._now()
        try:
            invitation = self._invitation_repository.get_by_token_hash(token_hash)
            if invitation is None:
                self._session.rollback()
                raise ActivationValidationNotFoundError

            active_attempt = self._attempt_repository.get_active_by_invitation(invitation.id)
            decision = self._rate_limit_repository.consume_existing_invitation(
                counter_kind=ActivationRateLimitKind.activation_validation,
                invitation_token_hash=token_hash,
                now=now,
            )
            if decision is None:
                self._session.rollback()
                raise ActivationValidationNotFoundError
            self._session.commit()
        except (
            ActivationValidationNotFoundError,
            ActivationValidationRateLimitedError,
        ):
            raise
        except SQLAlchemyError:
            self._session.rollback()
            raise ActivationValidationStorageUnavailableError from None

        if not decision.allowed:
            raise ActivationValidationRateLimitedError(decision.retry_after_seconds)

        if invitation.status in {
            InvitationStatus.used,
            InvitationStatus.revoked,
            InvitationStatus.expired,
        } or (invitation.status is InvitationStatus.pending and invitation.expires_at <= now):
            raise ActivationValidationUnavailableError
        if invitation.status is not InvitationStatus.pending or active_attempt is not None:
            raise ActivationValidationConflictError

        result = self._build_result(invitation)
        try:
            self._identity_provider.get_user(result.target_user_id)
        except SynapseUserNotFoundError:
            return result
        raise ActivationValidationConflictError

    def _build_result(self, invitation: Invitation) -> ActivationValidationResult:
        target_user_id = invitation.target_user_id
        if target_user_id is None or not isinstance(invitation.role, InvitationRole):
            raise ActivationValidationConflictError
        try:
            validated_user_id = validate_matrix_user_id(target_user_id)
            username, server_name = validated_user_id[1:].split(":", maxsplit=1)
            validated_username = validate_local_username(username)
            expected_user_id = build_local_matrix_user_id(
                validated_username,
                self._matrix_server_name,
            )
        except ValueError:
            raise ActivationValidationConflictError from None
        if server_name != self._matrix_server_name or expected_user_id != target_user_id:
            raise ActivationValidationConflictError

        return ActivationValidationResult(
            target_user_id=target_user_id,
            username=validated_username,
            role=invitation.role,
            expires_at=invitation.expires_at,
        )

    def _now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("clock must return a timezone-aware datetime")
        return now.astimezone(UTC)
