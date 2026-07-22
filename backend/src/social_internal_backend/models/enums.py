"""Utilitários compartilhados pelos enums persistentes."""

from enum import StrEnum


def enum_values(enum_class: type[StrEnum]) -> list[str]:
    """Persiste os valores públicos dos enums, não seus nomes Python."""

    return [member.value for member in enum_class]
