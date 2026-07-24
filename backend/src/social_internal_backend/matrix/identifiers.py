"""Validação conservadora de identificadores Matrix."""

import re

LOCAL_USERNAME_PATTERN = re.compile(
    r"^[a-z0-9][a-z0-9._-]{1,30}[a-z0-9]$",
    flags=re.ASCII,
)


def validate_local_username(username: str) -> str:
    """Valida o nome local corporativo sem normalizar seu conteúdo."""

    if LOCAL_USERNAME_PATTERN.fullmatch(username) is None:
        raise ValueError("invalid local username")
    return username


def validate_matrix_server_name(server_name: str) -> str:
    """Valida o domínio Matrix configurado sem interpretá-lo como URL."""

    if (
        not server_name
        or len(server_name) > 255
        or "://" in server_name
        or "/" in server_name
        or any(character.isspace() or not character.isprintable() for character in server_name)
    ):
        raise ValueError("invalid Matrix server name")
    return server_name


def build_local_matrix_user_id(username: str, server_name: str) -> str:
    """Constrói uma identidade Matrix local somente com valores validados."""

    validated_username = validate_local_username(username)
    validated_server_name = validate_matrix_server_name(server_name)
    return validate_matrix_user_id(f"@{validated_username}:{validated_server_name}")


def validate_matrix_user_id(matrix_user_id: str) -> str:
    """Aceita uma identidade Matrix completa sem tentar normalizá-la."""

    if len(matrix_user_id) > 255 or any(
        character.isspace() or not character.isprintable() for character in matrix_user_id
    ):
        raise ValueError("invalid Matrix user ID")
    if not matrix_user_id.startswith("@") or ":" not in matrix_user_id[1:]:
        raise ValueError("invalid Matrix user ID")

    localpart, server_name = matrix_user_id[1:].split(":", maxsplit=1)
    if not localpart or not server_name:
        raise ValueError("invalid Matrix user ID")
    return matrix_user_id
