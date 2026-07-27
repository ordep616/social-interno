"""Repositório de eventos que participa da transação do caso de uso."""

from datetime import datetime

from sqlalchemy.orm import Session

from social_internal_backend.models import AuditAction, AuditEvent, AuditResult


class AuditEventRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(
        self,
        *,
        actor_user_id: str,
        action: AuditAction,
        target: str,
        result: AuditResult,
        occurred_at: datetime,
    ) -> AuditEvent:
        event = AuditEvent(
            actor_user_id=actor_user_id,
            action=action,
            target=target,
            result=result,
            occurred_at=occurred_at,
        )
        self._session.add(event)
        self._session.flush()
        return event
