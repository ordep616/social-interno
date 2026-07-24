"""Validação e construção das identidades Matrix corporativas."""

import pytest

from social_internal_backend.matrix import (
    build_local_matrix_user_id,
    validate_local_username,
    validate_matrix_server_name,
)


@pytest.mark.parametrize(
    "username",
    [
        "a1b",
        "pedro",
        "pedro.ottavio",
        "grupo_admin-1",
        "a_b",
        "a" * 32,
    ],
)
def test_accepts_local_username_defined_by_dec_022(username: str) -> None:
    assert validate_local_username(username) == username


@pytest.mark.parametrize(
    "username",
    [
        "",
        "ab",
        "a" * 33,
        "Pedro",
        "pedrô",
        "pedro ottavio",
        ".pedro",
        "pedro.",
        "_pedro",
        "pedro_",
        "-pedro",
        "pedro-",
        "pedro@empresa",
        "pedro:empresa",
        " pedro",
        "pedro\n",
    ],
)
def test_rejects_invalid_local_username_without_normalizing(username: str) -> None:
    with pytest.raises(ValueError, match="invalid local username"):
        validate_local_username(username)


def test_builds_exact_local_matrix_user_id_without_normalizing() -> None:
    assert (
        build_local_matrix_user_id("pedro.ottavio", "matrix.empresa.test")
        == "@pedro.ottavio:matrix.empresa.test"
    )


@pytest.mark.parametrize(
    "server_name",
    [
        "",
        "https://matrix.empresa.test",
        "matrix.empresa.test/path",
        "matrix empresa.test",
        "matrix.empresa.test\n",
        "a" * 256,
    ],
)
def test_rejects_invalid_matrix_server_name(server_name: str) -> None:
    with pytest.raises(ValueError, match="invalid Matrix server name"):
        validate_matrix_server_name(server_name)


def test_rejects_constructed_matrix_user_id_longer_than_storage_contract() -> None:
    with pytest.raises(ValueError, match="invalid Matrix user ID"):
        build_local_matrix_user_id("pedro", "a" * 250)
