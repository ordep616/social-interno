"""Gera e resume tokens sem persistir o segredo original."""

from hashlib import sha256
from secrets import token_urlsafe

TOKEN_ENTROPY_BYTES = 32


def generate_invitation_token() -> str:
    """Gera um token URL-safe com 256 bits de entropia."""

    return token_urlsafe(TOKEN_ENTROPY_BYTES)


def hash_invitation_token(token: str) -> str:
    """Produz o hash SHA-256 usado para localizar um convite."""

    if not token:
        raise ValueError("invitation token must not be empty")
    return sha256(token.encode("utf-8")).hexdigest()
