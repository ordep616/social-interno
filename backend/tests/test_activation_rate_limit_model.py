"""Contrato ORM do limitador persistente da ativação."""

from datetime import UTC, datetime, timedelta

from social_internal_backend.models import ActivationRateLimit, ActivationRateLimitKind


def test_model_contains_only_approved_operational_fields() -> None:
    assert set(ActivationRateLimit.__table__.columns.keys()) == {
        "counter_kind",
        "invitation_token_hash",
        "window_started_at",
        "window_ends_at",
        "attempt_count",
        "expires_at",
    }


def test_model_accepts_separate_counter_kinds_without_secrets() -> None:
    started_at = datetime(2026, 7, 27, 12, tzinfo=UTC)
    counter = ActivationRateLimit(
        counter_kind=ActivationRateLimitKind.activation_validation,
        invitation_token_hash="a" * 64,
        window_started_at=started_at,
        window_ends_at=started_at + timedelta(minutes=15),
        attempt_count=1,
        expires_at=started_at + timedelta(hours=1, minutes=15),
    )

    assert counter.counter_kind is ActivationRateLimitKind.activation_validation
    assert counter.attempt_count == 1
    assert not hasattr(counter, "invitation_token")
    assert not hasattr(counter, "password")
    assert not hasattr(counter, "ip_address")
