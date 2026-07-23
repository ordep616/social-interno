"""Validação conservadora de identificadores Matrix."""


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
