"""Autorização corporativa mantida pelo serviço auxiliar."""

from social_internal_backend.authorization.bootstrap import (
    BootstrapAlreadyCompletedError,
    BootstrapResult,
    PlatformAdminBootstrapService,
)
from social_internal_backend.authorization.repository import UserRoleAssignmentRepository

__all__ = [
    "BootstrapAlreadyCompletedError",
    "BootstrapResult",
    "PlatformAdminBootstrapService",
    "UserRoleAssignmentRepository",
]
