"""Retomada administrativa sem repetir a criação da conta."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy.orm import Session

from social_internal_backend.models import RegistrationAttemptStatus
from social_internal_backend.registrations.repository import RegistrationAttemptRepository
from social_internal_backend.registrations.unit_of_work import RegistrationUnitOfWork
from social_internal_backend.synapse import SynapseUserNotFoundError

Clock = Callable[[], datetime]


class DeviceAdministrationProvider(Protocol):
    def get_device(self, *, user_id: str, device_id: str) -> None: ...
    def delete_device(self, *, user_id: str, device_id: str) -> None: ...


class ReconciliationNotFoundError(Exception):
    """A tentativa informada não existe."""


class ReconciliationStateError(Exception):
    """A tentativa não possui evidência suficiente para retomada automática."""


class ReconciliationDeviceStillPresentError(Exception):
    """O Synapse não confirmou a ausência do dispositivo."""


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    attempt_id: UUID
    user_id: str
    device_was_present: bool


def utc_now() -> datetime:
    return datetime.now(UTC)


class RegistrationReconciliationService:
    """Revoga somente o dispositivo conhecido e conclui a saga bloqueada."""

    def __init__(
        self,
        session: Session,
        *,
        admin_provider: DeviceAdministrationProvider,
        clock: Clock = utc_now,
    ) -> None:
        self._attempts = RegistrationAttemptRepository(session)
        self._uow = RegistrationUnitOfWork(session)
        self._admin_provider = admin_provider
        self._clock = clock

    def reconcile(self, attempt_id: UUID) -> ReconciliationResult:
        attempt = self._attempts.get(attempt_id)
        if attempt is None:
            raise ReconciliationNotFoundError
        if (
            attempt.status is not RegistrationAttemptStatus.reconciliation_required
            or not attempt.provisioning_device_id
        ):
            raise ReconciliationStateError

        device_was_present = True
        try:
            self._admin_provider.get_device(
                user_id=attempt.matrix_user_id,
                device_id=attempt.provisioning_device_id,
            )
        except SynapseUserNotFoundError:
            device_was_present = False
        else:
            self._admin_provider.delete_device(
                user_id=attempt.matrix_user_id,
                device_id=attempt.provisioning_device_id,
            )

        try:
            self._admin_provider.get_device(
                user_id=attempt.matrix_user_id,
                device_id=attempt.provisioning_device_id,
            )
        except SynapseUserNotFoundError:
            pass
        else:
            raise ReconciliationDeviceStillPresentError

        now = self._clock().astimezone(UTC)
        self._uow.record_provisioning_session_revoked(
            attempt_id=attempt.id,
            provisioning_device_id=attempt.provisioning_device_id,
            now=now,
        )
        self._uow.finalize(attempt_id=attempt.id, now=now)
        return ReconciliationResult(
            attempt_id=attempt.id,
            user_id=attempt.matrix_user_id,
            device_was_present=device_was_present,
        )
