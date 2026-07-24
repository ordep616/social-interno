"""Autorização corporativa mantida pelo serviço auxiliar."""

from social_internal_backend.authorization.bootstrap import (
    BootstrapAlreadyCompletedError,
    BootstrapResult,
    PlatformAdminBootstrapService,
)
from social_internal_backend.authorization.repository import UserRoleAssignmentRepository
from social_internal_backend.authorization.service import (
    AuthorizedPlatformAdmin,
    CorporateUserAccessDeniedError,
    PlatformAdminAccessDeniedError,
    PlatformAdminAuthorizationService,
    UserCapabilitiesContext,
    UserCapabilitiesService,
)

__all__ = [
    "BootstrapAlreadyCompletedError",
    "BootstrapResult",
    "AuthorizedPlatformAdmin",
    "CorporateUserAccessDeniedError",
    "PlatformAdminAccessDeniedError",
    "PlatformAdminAuthorizationService",
    "PlatformAdminBootstrapService",
    "UserCapabilitiesContext",
    "UserCapabilitiesService",
    "UserRoleAssignmentRepository",
]
