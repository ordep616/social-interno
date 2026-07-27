"""Gravação transacional curta de eventos administrativos."""

from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from social_internal_backend.audit.repository import AuditEventRepository
from social_internal_backend.models import AuditAction, AuditEvent, AuditResult

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC)


class AuditService:
    def __init__(self, session: Session, *, clock: Clock = utc_now) -> None:
        self._session = session
        self._repository = AuditEventRepository(session)
        self._clock = clock

    def record(
        self,
        *,
        actor_user_id: str,
        action: AuditAction,
        target: str,
        result: AuditResult,
    ) -> AuditEvent:
        try:
            event = self._repository.add(
                actor_user_id=actor_user_id,
                action=action,
                target=target,
                result=result,
                occurred_at=self._clock().astimezone(UTC),
            )
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
        return event
