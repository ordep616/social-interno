"""Atomicidade e restrições reais do limitador em PostgreSQL."""

import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Connection, Engine, create_engine, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from social_internal_backend.models import ActivationRateLimit, ActivationRateLimitKind
from social_internal_backend.rate_limits import ActivationRateLimitRepository

pytestmark = pytest.mark.postgres


@pytest.fixture(scope="module")
def postgres_engine() -> Iterator[Engine]:
    """Conecta somente ao PostgreSQL descartável explicitamente fornecido."""

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
    """Isola cenários de restrição em uma transação revertida."""

    with postgres_engine.connect() as database_connection:
        transaction = database_connection.begin()
        try:
            yield database_connection
        finally:
            transaction.rollback()


def insert_invitation(
    connection: Connection,
    *,
    invitation_id: UUID,
    token_hash: str,
) -> None:
    """Cria um convite conhecido sem armazenar o token original."""

    now = datetime(2026, 7, 27, 12, tzinfo=UTC)
    connection.execute(
        text(
            """
            INSERT INTO invitations (
                id,
                token_hash,
                role,
                status,
                created_by,
                target_user_id,
                created_at,
                expires_at
            )
            VALUES (
                :id,
                :token_hash,
                'user',
                'pending',
                '@admin:localhost',
                :target_user_id,
                :created_at,
                :expires_at
            )
            """
        ),
        {
            "id": invitation_id,
            "token_hash": token_hash,
            "target_user_id": f"@user-{invitation_id.hex}:localhost",
            "created_at": now,
            "expires_at": now + timedelta(hours=24),
        },
    )


def test_migration_contains_only_approved_fields_constraints_and_index(
    postgres_engine: Engine,
) -> None:
    inspector = inspect(postgres_engine)

    assert {column["name"] for column in inspector.get_columns("activation_rate_limits")} == {
        "counter_kind",
        "invitation_token_hash",
        "window_started_at",
        "window_ends_at",
        "attempt_count",
        "expires_at",
    }
    assert {
        constraint["name"]
        for constraint in inspector.get_check_constraints("activation_rate_limits")
    } == {
        "ck_activation_rate_limits_attempt_count_positive",
        "ck_activation_rate_limits_counter_kind",
        "ck_activation_rate_limits_retention",
        "ck_activation_rate_limits_token_hash_sha256",
        "ck_activation_rate_limits_window_duration",
    }
    assert {index["name"] for index in inspector.get_indexes("activation_rate_limits")} == {
        "ix_activation_rate_limits_expires_at",
    }


def insert_counter(
    connection: Connection,
    *,
    token_hash: str,
    window_started_at: datetime,
    window_ends_at: datetime,
    attempt_count: int,
    expires_at: datetime,
) -> None:
    """Insere diretamente para que o PostgreSQL valide as invariantes."""

    connection.execute(
        text(
            """
            INSERT INTO activation_rate_limits (
                counter_kind,
                invitation_token_hash,
                window_started_at,
                window_ends_at,
                attempt_count,
                expires_at
            )
            VALUES (
                'activation_validation',
                :token_hash,
                :window_started_at,
                :window_ends_at,
                :attempt_count,
                :expires_at
            )
            """
        ),
        {
            "token_hash": token_hash,
            "window_started_at": window_started_at,
            "window_ends_at": window_ends_at,
            "attempt_count": attempt_count,
            "expires_at": expires_at,
        },
    )


def test_database_rejects_counter_for_unknown_invitation(connection: Connection) -> None:
    started_at = datetime(2026, 7, 27, 12, tzinfo=UTC)

    with pytest.raises(IntegrityError), connection.begin_nested():
        insert_counter(
            connection,
            token_hash="f" * 64,
            window_started_at=started_at,
            window_ends_at=started_at + timedelta(minutes=15),
            attempt_count=1,
            expires_at=started_at + timedelta(hours=1, minutes=15),
        )


@pytest.mark.parametrize(
    ("window_duration", "attempt_count", "retention"),
    [
        (timedelta(minutes=14), 1, timedelta(hours=1)),
        (timedelta(minutes=15), 0, timedelta(hours=1)),
        (timedelta(minutes=15), 1, timedelta(minutes=59)),
    ],
)
def test_database_rejects_invalid_window_count_and_retention(
    connection: Connection,
    window_duration: timedelta,
    attempt_count: int,
    retention: timedelta,
) -> None:
    invitation_id = uuid4()
    token_hash = invitation_id.hex * 2
    started_at = datetime(2026, 7, 27, 12, tzinfo=UTC)
    ended_at = started_at + window_duration
    insert_invitation(connection, invitation_id=invitation_id, token_hash=token_hash)

    with pytest.raises(IntegrityError), connection.begin_nested():
        insert_counter(
            connection,
            token_hash=token_hash,
            window_started_at=started_at,
            window_ends_at=ended_at,
            attempt_count=attempt_count,
            expires_at=ended_at + retention,
        )


def test_separate_limits_windows_and_cleanup(connection: Connection) -> None:
    invitation_id = uuid4()
    token_hash = invitation_id.hex * 2
    insert_invitation(connection, invitation_id=invitation_id, token_hash=token_hash)
    session = Session(bind=connection, expire_on_commit=False)
    repository = ActivationRateLimitRepository(session)
    first_window = datetime(2026, 7, 27, 12, 1, tzinfo=UTC)

    for attempt_number in range(1, 12):
        decision = repository.consume_existing_invitation(
            counter_kind=ActivationRateLimitKind.activation_validation,
            invitation_token_hash=token_hash,
            now=first_window,
        )
        assert decision is not None
        assert decision.allowed is (attempt_number <= 10)
        assert decision.attempt_count == min(attempt_number, 11)

    registration = repository.consume_existing_invitation(
        counter_kind=ActivationRateLimitKind.registration,
        invitation_token_hash=token_hash,
        now=first_window,
    )
    next_window = repository.consume_existing_invitation(
        counter_kind=ActivationRateLimitKind.activation_validation,
        invitation_token_hash=token_hash,
        now=datetime(2026, 7, 27, 12, 16, tzinfo=UTC),
    )

    assert registration is not None and registration.attempt_count == 1
    assert next_window is not None and next_window.attempt_count == 1
    assert repository.delete_expired(now=datetime(2026, 7, 27, 13, 14, tzinfo=UTC)) == 0
    assert repository.delete_expired(now=datetime(2026, 7, 27, 13, 15, tzinfo=UTC)) == 2
    assert repository.delete_expired(now=datetime(2026, 7, 27, 13, 15, tzinfo=UTC)) == 0


def test_concurrent_consumption_is_atomic_and_bounded(postgres_engine: Engine) -> None:
    invitation_id = uuid4()
    token_hash = invitation_id.hex * 2
    now = datetime(2026, 7, 27, 16, 1, tzinfo=UTC)

    with postgres_engine.begin() as connection:
        insert_invitation(connection, invitation_id=invitation_id, token_hash=token_hash)

    def consume_once() -> bool:
        with Session(postgres_engine) as session:
            decision = ActivationRateLimitRepository(session).consume_existing_invitation(
                counter_kind=ActivationRateLimitKind.activation_validation,
                invitation_token_hash=token_hash,
                now=now,
            )
            session.commit()
            assert decision is not None
            return decision.allowed

    try:
        with ThreadPoolExecutor(max_workers=12) as executor:
            allowed = list(executor.map(lambda _: consume_once(), range(12)))

        with Session(postgres_engine) as session:
            stored_count = session.scalar(
                select(ActivationRateLimit.attempt_count).where(
                    ActivationRateLimit.counter_kind
                    == ActivationRateLimitKind.activation_validation,
                    ActivationRateLimit.invitation_token_hash == token_hash,
                )
            )

        assert sum(allowed) == 10
        assert stored_count == 11
    finally:
        with postgres_engine.begin() as connection:
            connection.execute(
                text(
                    "DELETE FROM activation_rate_limits WHERE invitation_token_hash = :token_hash"
                ),
                {"token_hash": token_hash},
            )
            connection.execute(
                text("DELETE FROM invitations WHERE id = :invitation_id"),
                {"invitation_id": invitation_id},
            )
