"""Integrações suportadas com o homeserver Synapse."""

from social_internal_backend.synapse.admin_client import (
    CreatedSynapseUser,
    InvalidSynapseAdminCredentialError,
    SynapseAdminClient,
    SynapseAdminProtocolError,
    SynapseAdminRateLimitedError,
    SynapseAdminUnavailableError,
    SynapseUser,
    SynapseUserAlreadyExistsError,
    SynapseUserNotFoundError,
)
from social_internal_backend.synapse.client import (
    InvalidMatrixAccessTokenError,
    MatrixIdentity,
    SynapseClient,
    SynapseProtocolError,
    SynapseRateLimitedError,
    SynapseUnavailableError,
)

__all__ = [
    "CreatedSynapseUser",
    "InvalidSynapseAdminCredentialError",
    "InvalidMatrixAccessTokenError",
    "MatrixIdentity",
    "SynapseAdminClient",
    "SynapseAdminProtocolError",
    "SynapseAdminRateLimitedError",
    "SynapseAdminUnavailableError",
    "SynapseClient",
    "SynapseProtocolError",
    "SynapseRateLimitedError",
    "SynapseUnavailableError",
    "SynapseUser",
    "SynapseUserAlreadyExistsError",
    "SynapseUserNotFoundError",
]
