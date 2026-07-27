"""Persistência e futura orquestração do cadastro controlado."""

from social_internal_backend.registrations.reconciliation import (
    ReconciliationDeviceStillPresentError,
    ReconciliationNotFoundError,
    ReconciliationResult,
    ReconciliationStateError,
    RegistrationReconciliationService,
)
from social_internal_backend.registrations.repository import RegistrationAttemptRepository
from social_internal_backend.registrations.service import (
    RegistrationConflictError,
    RegistrationNotFoundError,
    RegistrationPasswordPolicyError,
    RegistrationRateLimitedError,
    RegistrationResult,
    RegistrationService,
    RegistrationStorageUnavailableError,
    RegistrationUnavailableError,
    RegistrationUpstreamInvalidResponseError,
    RegistrationUpstreamUnavailableError,
)
from social_internal_backend.registrations.unit_of_work import (
    RegistrationCheckpointConflictError,
    RegistrationFinalization,
    RegistrationFinalizationConflictError,
    RegistrationIdentityConflictError,
    RegistrationRelease,
    RegistrationReleaseConflictError,
    RegistrationReservation,
    RegistrationReservationConflictError,
    RegistrationTransactionConflictError,
    RegistrationUnitOfWork,
)

__all__ = [
    "RegistrationAttemptRepository",
    "ReconciliationDeviceStillPresentError",
    "ReconciliationNotFoundError",
    "ReconciliationResult",
    "ReconciliationStateError",
    "RegistrationReconciliationService",
    "RegistrationConflictError",
    "RegistrationCheckpointConflictError",
    "RegistrationFinalization",
    "RegistrationFinalizationConflictError",
    "RegistrationIdentityConflictError",
    "RegistrationNotFoundError",
    "RegistrationPasswordPolicyError",
    "RegistrationRateLimitedError",
    "RegistrationResult",
    "RegistrationService",
    "RegistrationStorageUnavailableError",
    "RegistrationUnavailableError",
    "RegistrationUpstreamInvalidResponseError",
    "RegistrationUpstreamUnavailableError",
    "RegistrationRelease",
    "RegistrationReleaseConflictError",
    "RegistrationReservation",
    "RegistrationReservationConflictError",
    "RegistrationTransactionConflictError",
    "RegistrationUnitOfWork",
]
