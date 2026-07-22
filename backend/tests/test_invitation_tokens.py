"""Segurança dos tokens de convite."""

import re
from hashlib import sha256

import pytest

from social_internal_backend.invitations.tokens import (
    TOKEN_ENTROPY_BYTES,
    generate_invitation_token,
    hash_invitation_token,
)


def test_generates_distinct_url_safe_tokens_with_256_bits_of_entropy() -> None:
    first = generate_invitation_token()
    second = generate_invitation_token()

    assert TOKEN_ENTROPY_BYTES == 32
    assert first != second
    assert len(first) == 43
    assert re.fullmatch(r"[A-Za-z0-9_-]+", first)


def test_hashes_token_with_sha256_without_returning_the_original() -> None:
    opaque_value = "valor-opaco-de-teste"
    digest = hash_invitation_token(opaque_value)

    assert digest == sha256(opaque_value.encode("utf-8")).hexdigest()
    assert len(digest) == 64
    assert opaque_value not in digest


def test_rejects_empty_token_before_hashing() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        hash_invitation_token("")
