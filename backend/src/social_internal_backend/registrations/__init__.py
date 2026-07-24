"""Persistência e futura orquestração do cadastro controlado."""

from social_internal_backend.registrations.repository import RegistrationAttemptRepository
from social_internal_backend.registrations.unit_of_work import (
    RegistrationCheckpointConflictError,
    RegistrationFinalization,
    RegistrationFinalizationConflictError,
    RegistrationRelease,
    RegistrationReleaseConflictError,
    RegistrationReservation,
    RegistrationReservationConflictError,
    RegistrationTransactionConflictError,
    RegistrationUnitOfWork,
)

__all__ = [
    "RegistrationAttemptRepository",
    "RegistrationCheckpointConflictError",
    "RegistrationFinalization",
    "RegistrationFinalizationConflictError",
    "RegistrationRelease",
    "RegistrationReleaseConflictError",
    "RegistrationReservation",
    "RegistrationReservationConflictError",
    "RegistrationTransactionConflictError",
    "RegistrationUnitOfWork",
]
