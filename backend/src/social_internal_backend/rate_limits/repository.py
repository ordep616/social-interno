"""Incremento atômico e limpeza dos limites de ativação."""

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import ceil

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from social_internal_backend.models import (
    ActivationRateLimit,
    ActivationRateLimitKind,
    Invitation,
)

RATE_LIMIT_WINDOW = timedelta(minutes=15)
RATE_LIMIT_RETENTION = timedelta(hours=1)
ACTIVATION_RATE_LIMITS = {
    ActivationRateLimitKind.activation_validation: 10,
    ActivationRateLimitKind.registration: 5,
}
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class ActivationRateLimitDecision:
    """Resultado sanitizado do consumo de uma tentativa."""

    allowed: bool
    attempt_count: int
    limit: int
    retry_after_seconds: int
    window_ends_at: datetime


def fixed_window_bounds(now: datetime) -> tuple[datetime, datetime]:
    """Calcula a janela UTC de 15 minutos sem depender do relógio do banco."""

    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")

    normalized = now.astimezone(UTC)
    started_at = normalized.replace(
        minute=(normalized.minute // 15) * 15,
        second=0,
        microsecond=0,
    )
    return started_at, started_at + RATE_LIMIT_WINDOW


class ActivationRateLimitRepository:
    """Persiste apenas contadores associados a convites conhecidos."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def consume_existing_invitation(
        self,
        *,
        counter_kind: ActivationRateLimitKind,
        invitation_token_hash: str,
        now: datetime,
    ) -> ActivationRateLimitDecision | None:
        """Incrementa atomicamente ou retorna ``None`` para hash desconhecido."""

        if _SHA256_PATTERN.fullmatch(invitation_token_hash) is None:
            raise ValueError("invitation_token_hash must be a lowercase SHA-256 hash")

        invitation_exists = self._session.scalar(
            select(Invitation.id).where(Invitation.token_hash == invitation_token_hash)
        )
        if invitation_exists is None:
            return None

        limit = ACTIVATION_RATE_LIMITS[counter_kind]
        window_started_at, window_ends_at = fixed_window_bounds(now)
        expires_at = window_ends_at + RATE_LIMIT_RETENTION

        insert_statement = insert(ActivationRateLimit).values(
            counter_kind=counter_kind,
            invitation_token_hash=invitation_token_hash,
            window_started_at=window_started_at,
            window_ends_at=window_ends_at,
            attempt_count=1,
            expires_at=expires_at,
        )
        upsert_statement = insert_statement.on_conflict_do_update(
            index_elements=(
                ActivationRateLimit.counter_kind,
                ActivationRateLimit.invitation_token_hash,
                ActivationRateLimit.window_started_at,
            ),
            set_={
                "attempt_count": func.least(
                    ActivationRateLimit.attempt_count + 1,
                    limit + 1,
                ),
            },
        ).returning(ActivationRateLimit.attempt_count)

        attempt_count = self._session.execute(upsert_statement).scalar_one()
        retry_after_seconds = max(
            1,
            ceil((window_ends_at - now.astimezone(UTC)).total_seconds()),
        )
        return ActivationRateLimitDecision(
            allowed=attempt_count <= limit,
            attempt_count=attempt_count,
            limit=limit,
            retry_after_seconds=retry_after_seconds,
            window_ends_at=window_ends_at,
        )

    def delete_expired(self, *, now: datetime) -> int:
        """Remove de forma idempotente os contadores após a retenção aprovada."""

        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now must be timezone-aware")

        statement = (
            delete(ActivationRateLimit)
            .where(ActivationRateLimit.expires_at <= now.astimezone(UTC))
            .returning(ActivationRateLimit.invitation_token_hash)
        )
        return len(self._session.scalars(statement).all())
