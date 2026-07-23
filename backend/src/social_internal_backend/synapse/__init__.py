"""Integrações suportadas com o homeserver Synapse."""

from social_internal_backend.synapse.client import (
    InvalidMatrixAccessTokenError,
    MatrixIdentity,
    SynapseClient,
    SynapseProtocolError,
    SynapseRateLimitedError,
    SynapseUnavailableError,
)

__all__ = [
    "InvalidMatrixAccessTokenError",
    "MatrixIdentity",
    "SynapseClient",
    "SynapseProtocolError",
    "SynapseRateLimitedError",
    "SynapseUnavailableError",
]
