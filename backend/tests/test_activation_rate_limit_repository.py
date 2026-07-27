"""Contrato SQLAlchemy do repositório do limitador."""

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from social_internal_backend.models import ActivationRateLimitKind
from social_internal_backend.rate_limits import (
    ActivationRateLimitRepository,
    fixed_window_bounds,
)


def test_fixed_window_uses_utc_quarter_hour() -> None:
    started_at, ended_at = fixed_window_bounds(
        datetime(2026, 7, 27, 12, 29, 59, 999999, tzinfo=UTC)
    )

    assert started_at == datetime(2026, 7, 27, 12, 15, tzinfo=UTC)
    assert ended_at == datetime(2026, 7, 27, 12, 30, tzinfo=UTC)


def test_fixed_window_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        fixed_window_bounds(datetime(2026, 7, 27, 12))


def test_unknown_invitation_does_not_create_counter() -> None:
    session = MagicMock(spec=Session)
    session.scalar.return_value = None
    repository = ActivationRateLimitRepository(session)

    result = repository.consume_existing_invitation(
        counter_kind=ActivationRateLimitKind.activation_validation,
        invitation_token_hash="a" * 64,
        now=datetime(2026, 7, 27, 12, tzinfo=UTC),
    )

    assert result is None
    session.execute.assert_not_called()
    session.commit.assert_not_called()


def test_consume_returns_sanitized_decision_without_committing() -> None:
    session = MagicMock(spec=Session)
    session.scalar.return_value = uuid4()
    session.execute.return_value.scalar_one.return_value = 10
    repository = ActivationRateLimitRepository(session)

    result = repository.consume_existing_invitation(
        counter_kind=ActivationRateLimitKind.activation_validation,
        invitation_token_hash="b" * 64,
        now=datetime(2026, 7, 27, 12, 14, 30, tzinfo=UTC),
    )

    assert result is not None
    assert result.allowed is True
    assert result.attempt_count == 10
    assert result.limit == 10
    assert result.retry_after_seconds == 30
    session.commit.assert_not_called()


def test_consume_rejects_invalid_hash_before_database_access() -> None:
    session = MagicMock(spec=Session)
    repository = ActivationRateLimitRepository(session)

    with pytest.raises(ValueError, match="lowercase SHA-256"):
        repository.consume_existing_invitation(
            counter_kind=ActivationRateLimitKind.registration,
            invitation_token_hash="x" * 63,
            now=datetime(2026, 7, 27, 12, tzinfo=UTC),
        )

    session.scalar.assert_not_called()
    session.execute.assert_not_called()


def test_cleanup_is_idempotent_and_does_not_commit() -> None:
    session = MagicMock(spec=Session)
    session.scalars.return_value.all.side_effect = [["a" * 64, "b" * 64], []]
    repository = ActivationRateLimitRepository(session)
    now = datetime(2026, 7, 27, 14, tzinfo=UTC)

    assert repository.delete_expired(now=now) == 2
    assert repository.delete_expired(now=now) == 0
    session.commit.assert_not_called()


def test_cleanup_rejects_naive_datetime() -> None:
    repository = ActivationRateLimitRepository(MagicMock(spec=Session))

    with pytest.raises(ValueError, match="timezone-aware"):
        repository.delete_expired(now=datetime(2026, 7, 27, 14))
