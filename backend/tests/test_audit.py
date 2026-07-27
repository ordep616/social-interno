"""Auditoria estruturada sem campos sensíveis."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from social_internal_backend.audit import AuditService
from social_internal_backend.models import AuditAction, AuditEvent, AuditResult

NOW = datetime(2026, 7, 27, 18, tzinfo=UTC)


def test_audit_model_has_only_approved_operational_fields() -> None:
    assert {column.name for column in AuditEvent.__table__.columns} == {
        "id",
        "actor_user_id",
        "action",
        "target",
        "result",
        "occurred_at",
    }


def test_audit_service_commits_sanitized_event() -> None:
    session = MagicMock()
    service = AuditService(session, clock=lambda: NOW)
    repository = MagicMock()
    event = object()
    repository.add.return_value = event
    service._repository = repository

    result = service.record(
        actor_user_id="@admin:localhost",
        action=AuditAction.invitation_created,
        target="@employee:localhost",
        result=AuditResult.success,
    )

    assert result is event
    repository.add.assert_called_once_with(
        actor_user_id="@admin:localhost",
        action=AuditAction.invitation_created,
        target="@employee:localhost",
        result=AuditResult.success,
        occurred_at=NOW,
    )
    session.commit.assert_called_once()


def test_audit_service_rolls_back_storage_failure() -> None:
    session = MagicMock()
    service = AuditService(session)
    service._repository = MagicMock()
    service._repository.add.side_effect = RuntimeError

    with pytest.raises(RuntimeError):
        service.record(
            actor_user_id="@admin:localhost",
            action=AuditAction.password_reset,
            target="@employee:localhost",
            result=AuditResult.failure,
        )
    session.rollback.assert_called_once()
