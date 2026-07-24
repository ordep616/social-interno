"""Primitivas compartilhadas do protocolo Matrix."""

from social_internal_backend.matrix.identifiers import (
    build_local_matrix_user_id,
    validate_local_username,
    validate_matrix_server_name,
    validate_matrix_user_id,
)

__all__ = [
    "build_local_matrix_user_id",
    "validate_local_username",
    "validate_matrix_server_name",
    "validate_matrix_user_id",
]
