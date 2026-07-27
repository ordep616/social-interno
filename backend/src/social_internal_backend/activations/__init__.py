"""Pré-validação e futura orquestração dos fluxos de ativação."""

from social_internal_backend.activations.validation_service import (
    ActivationValidationConflictError,
    ActivationValidationNotFoundError,
    ActivationValidationRateLimitedError,
    ActivationValidationResult,
    ActivationValidationService,
    ActivationValidationStorageUnavailableError,
    ActivationValidationUnavailableError,
)

__all__ = [
    "ActivationValidationConflictError",
    "ActivationValidationNotFoundError",
    "ActivationValidationRateLimitedError",
    "ActivationValidationResult",
    "ActivationValidationService",
    "ActivationValidationStorageUnavailableError",
    "ActivationValidationUnavailableError",
]
