"""Contrato real da trilha de auditoria no PostgreSQL isolado."""

import os
from collections.abc import Iterator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import Connection, Engine, create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

pytestmark = pytest.mark.postgres


@pytest.fixture(scope="module")
def postgres_engine() -> Iterator[Engine]:
    database_url = os.environ.get("BACKEND_TEST_DATABASE_URL")
    if database_url is None:
        pytest.skip("BACKEND_TEST_DATABASE_URL is not configured")
    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def connection(postgres_engine: Engine) -> Iterator[Connection]:
    with postgres_engine.connect() as database_connection:
        transaction = database_connection.begin()
        try:
            yield database_connection
        finally:
            transaction.rollback()


def test_audit_migration_has_only_approved_fields_and_indexes(
    postgres_engine: Engine,
) -> None:
    inspector = inspect(postgres_engine)
    assert {column["name"] for column in inspector.get_columns("audit_events")} == {
        "id",
        "actor_user_id",
        "action",
        "target",
        "result",
        "occurred_at",
    }
    assert {index["name"] for index in inspector.get_indexes("audit_events")} == {
        "ix_audit_events_occurred_at",
        "ix_audit_events_target_occurred_at",
    }


@pytest.mark.parametrize(
    ("action", "result", "target"),
    [
        ("unknown_action", "success", "@employee:localhost"),
        ("invitation_created", "unknown_result", "@employee:localhost"),
        ("invitation_created", "success", ""),
    ],
)
def test_audit_constraints_reject_unapproved_values(
    connection: Connection,
    action: str,
    result: str,
    target: str,
) -> None:
    with pytest.raises(IntegrityError):
        connection.execute(
            text(
                """
                INSERT INTO audit_events (
                    id, actor_user_id, action, target, result, occurred_at
                )
                VALUES (
                    :id, '@admin:localhost', :action, :target, :result, :occurred_at
                )
                """
            ),
            {
                "id": uuid4(),
                "action": action,
                "target": target,
                "result": result,
                "occurred_at": datetime(2026, 7, 27, 18, tzinfo=UTC),
            },
        )
