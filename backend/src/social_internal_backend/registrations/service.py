"""Orquestração durável da ativação de uma identidade predefinida."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from pydantic import SecretStr
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from social_internal_backend.invitations.repository import InvitationRepository
from social_internal_backend.invitations.tokens import hash_invitation_token
from social_internal_backend.matrix import validate_local_username, validate_matrix_user_id
from social_internal_backend.models import (
    ActivationRateLimitKind,
    InvitationStatus,
)
from social_internal_backend.rate_limits import (
    ActivationRateLimitDecision,
    ActivationRateLimitRepository,
)
from social_internal_backend.registrations.unit_of_work import RegistrationUnitOfWork
from social_internal_backend.synapse import (
    InvalidMatrixAccessTokenError,
    MatrixIdentity,
    ProvisioningSession,
    SynapseRegistrationConflictError,
    SynapseRegistrationProtocolError,
    SynapseRegistrationUnavailableError,
    SynapseUserNotFoundError,
)

Clock = Callable[[], datetime]


class RegistrationProvider(Protocol):
    def register(self, *, username: str, password: SecretStr) -> ProvisioningSession: ...


class IdentityProvider(Protocol):
    def whoami(self, access_token: str) -> MatrixIdentity: ...


class AdminProvider(Protocol):
    def get_user(self, user_id: str) -> object: ...
    def get_device(self, *, user_id: str, device_id: str) -> None: ...
    def delete_device(self, *, user_id: str, device_id: str) -> None: ...


class RegistrationNotFoundError(Exception): ...


class RegistrationUnavailableError(Exception): ...


class RegistrationConflictError(Exception): ...


class RegistrationPasswordPolicyError(Exception): ...


class RegistrationRateLimitedError(Exception):
    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds


class RegistrationStorageUnavailableError(Exception): ...


class RegistrationUpstreamInvalidResponseError(Exception): ...


class RegistrationUpstreamUnavailableError(Exception): ...


@dataclass(frozen=True, slots=True)
class RegistrationResult:
    user_id: str


def utc_now() -> datetime:
    return datetime.now(UTC)


class RegistrationService:
    """Coordena transações curtas e efeitos externos sem persistir segredos."""

    def __init__(
        self,
        session: Session,
        *,
        registration_provider: RegistrationProvider,
        identity_provider: IdentityProvider,
        admin_provider: AdminProvider,
        matrix_server_name: str,
        clock: Clock = utc_now,
    ) -> None:
        self._session = session
        self._registration_provider = registration_provider
        self._identity_provider = identity_provider
        self._admin_provider = admin_provider
        self._server_name = matrix_server_name
        self._clock = clock
        self._invitations = InvitationRepository(session)
        self._limits = ActivationRateLimitRepository(session)
        self._uow = RegistrationUnitOfWork(session)

    def register(self, invitation_token: str, password: SecretStr) -> RegistrationResult:
        password_value = password.get_secret_value()
        if not 15 <= len(password_value) <= 128:
            raise RegistrationPasswordPolicyError
        token_hash = hash_invitation_token(invitation_token)
        now = self._now()
        try:
            invitation = self._invitations.get_by_token_hash(token_hash)
            if invitation is None:
                self._session.rollback()
                raise RegistrationNotFoundError
            decision = self._limits.consume_existing_invitation(
                counter_kind=ActivationRateLimitKind.registration,
                invitation_token_hash=token_hash,
                now=now,
            )
            if decision is None:
                self._session.rollback()
                raise RegistrationNotFoundError
            self._session.commit()
        except RegistrationNotFoundError, RegistrationRateLimitedError:
            raise
        except SQLAlchemyError:
            self._session.rollback()
            raise RegistrationStorageUnavailableError from None
        self._enforce_limit(decision)
        if invitation.status in {
            InvitationStatus.used,
            InvitationStatus.revoked,
            InvitationStatus.expired,
        } or (invitation.status is InvitationStatus.pending and invitation.expires_at <= now):
            raise RegistrationUnavailableError
        if invitation.status is not InvitationStatus.pending:
            raise RegistrationConflictError

        reservation = self._uow.reserve(token_hash=token_hash, now=self._now())
        target_user_id = reservation.attempt.matrix_user_id
        username = self._username(target_user_id)
        try:
            self._admin_provider.get_user(target_user_id)
        except SynapseUserNotFoundError:
            pass
        else:
            self._uow.conflict_identity(
                attempt_id=reservation.attempt.id,
                now=self._now(),
            )
            raise RegistrationConflictError

        try:
            provisioning = self._registration_provider.register(
                username=username,
                password=password,
            )
        except SynapseRegistrationConflictError:
            self._uow.conflict_identity(
                attempt_id=reservation.attempt.id,
                now=self._now(),
            )
            raise RegistrationConflictError from None
        except SynapseRegistrationUnavailableError as error:
            self._handle_creation_failure(reservation.attempt.id, error.ambiguous)
            raise RegistrationUpstreamUnavailableError from None
        except SynapseRegistrationProtocolError as error:
            self._handle_creation_failure(reservation.attempt.id, error.ambiguous)
            raise RegistrationUpstreamInvalidResponseError from None

        access_token = provisioning.access_token.get_secret_value()
        try:
            identity = self._identity_provider.whoami(access_token)
            if (
                provisioning.user_id != target_user_id
                or identity.user_id != target_user_id
                or identity.device_id != provisioning.device_id
                or identity.is_guest
            ):
                raise RegistrationUpstreamInvalidResponseError
            self._uow.record_synapse_created(
                attempt_id=reservation.attempt.id,
                provisioning_device_id=provisioning.device_id,
                now=self._now(),
            )
        except Exception as error:
            self._record_reconciliation(reservation.attempt.id, "creation_validation_failed")
            if isinstance(error, RegistrationUpstreamInvalidResponseError):
                raise
            raise RegistrationUpstreamUnavailableError from None

        try:
            self._admin_provider.get_device(
                user_id=target_user_id,
                device_id=provisioning.device_id,
            )
            self._admin_provider.delete_device(
                user_id=target_user_id,
                device_id=provisioning.device_id,
            )
            try:
                self._admin_provider.get_device(
                    user_id=target_user_id,
                    device_id=provisioning.device_id,
                )
            except SynapseUserNotFoundError:
                pass
            else:
                raise RegistrationUpstreamInvalidResponseError
            try:
                self._identity_provider.whoami(access_token)
            except InvalidMatrixAccessTokenError:
                pass
            else:
                raise RegistrationUpstreamInvalidResponseError
            self._uow.record_provisioning_session_revoked(
                attempt_id=reservation.attempt.id,
                provisioning_device_id=provisioning.device_id,
                now=self._now(),
            )
        except Exception as error:
            self._record_reconciliation(reservation.attempt.id, "session_revocation_failed")
            if isinstance(error, RegistrationUpstreamInvalidResponseError):
                raise
            raise RegistrationUpstreamUnavailableError from None
        finally:
            del access_token

        finalization = self._uow.finalize(
            attempt_id=reservation.attempt.id,
            now=self._now(),
        )
        return RegistrationResult(user_id=finalization.attempt.matrix_user_id)

    def _handle_creation_failure(self, attempt_id: UUID, ambiguous: bool) -> None:
        if ambiguous:
            self._record_reconciliation(attempt_id, "creation_ambiguous")
        else:
            self._uow.release(
                attempt_id=attempt_id,
                failure_code="creation_unavailable",
                now=self._now(),
            )

    def _record_reconciliation(self, attempt_id: UUID, failure_code: str) -> None:
        self._uow.record_reconciliation_required(
            attempt_id=attempt_id,
            failure_code=failure_code,
            now=self._now(),
        )

    def _username(self, user_id: str) -> str:
        validated = validate_matrix_user_id(user_id)
        username, server_name = validated[1:].split(":", maxsplit=1)
        if server_name != self._server_name:
            raise RegistrationConflictError
        return validate_local_username(username)

    @staticmethod
    def _enforce_limit(decision: ActivationRateLimitDecision) -> None:
        if not decision.allowed:
            raise RegistrationRateLimitedError(decision.retry_after_seconds)

    def _now(self) -> datetime:
        return self._clock().astimezone(UTC)
