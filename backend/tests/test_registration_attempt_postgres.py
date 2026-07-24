"""Restrições reais das tentativas em um PostgreSQL isolado."""

import os
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import Connection, Engine, create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from social_internal_backend.models import (
    InvitationRole,
    RegistrationAttempt,
    RegistrationAttemptStatus,
)
from social_internal_backend.registrations import RegistrationAttemptRepository

pytestmark = pytest.mark.postgres

INVITATION_ONE = UUID("10000000-0000-0000-0000-000000000001")
INVITATION_TWO = UUID("10000000-0000-0000-0000-000000000002")
ATTEMPT_ONE = UUID("20000000-0000-0000-0000-000000000001")
ATTEMPT_TWO = UUID("20000000-0000-0000-0000-000000000002")
ATTEMPT_THREE = UUID("20000000-0000-0000-0000-000000000003")
MISSING_INVITATION = UUID("10000000-0000-0000-0000-000000000099")


@pytest.fixture(scope="module")
def postgres_engine() -> Iterator[Engine]:
    """Conecta somente ao banco descartável explicitamente fornecido."""

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
    """Isola cada cenário em uma transação revertida ao final."""

    with postgres_engine.connect() as database_connection:
        transaction = database_connection.begin()
        try:
            yield database_connection
        finally:
            transaction.rollback()


def insert_invitation(connection: Connection, invitation_id: UUID, token_character: str) -> None:
    """Cria o vínculo mínimo exigido pela chave estrangeira."""

    now = datetime(2026, 7, 23, 12, tzinfo=UTC)
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
                'processing',
                '@admin:localhost',
                :target_user_id,
                :created_at,
                :expires_at
            )
            """
        ),
        {
            "id": invitation_id,
            "token_hash": token_character * 64,
            "target_user_id": f"@user-{token_character}:localhost",
            "created_at": now,
            "expires_at": now + timedelta(hours=24),
        },
    )


def insert_attempt(
    connection: Connection,
    *,
    attempt_id: UUID,
    invitation_id: UUID,
    matrix_user_id: str,
    status: str = "processing",
    provisioning_device_id: str | None = None,
    provisioning_session_revoked_at: datetime | None = None,
    completed_at: datetime | None = None,
    failure_code: str | None = None,
) -> None:
    """Insere diretamente para que o PostgreSQL avalie todas as restrições."""

    now = datetime(2026, 7, 23, 12, tzinfo=UTC)
    connection.execute(
        text(
            """
            INSERT INTO registration_attempts (
                id,
                invitation_id,
                matrix_user_id,
                role,
                status,
                created_at,
                updated_at,
                provisioning_device_id,
                provisioning_session_revoked_at,
                completed_at,
                failure_code
            )
            VALUES (
                :id,
                :invitation_id,
                :matrix_user_id,
                'user',
                :status,
                :created_at,
                :updated_at,
                :provisioning_device_id,
                :provisioning_session_revoked_at,
                :completed_at,
                :failure_code
            )
            """
        ),
        {
            "id": attempt_id,
            "invitation_id": invitation_id,
            "matrix_user_id": matrix_user_id,
            "status": status,
            "created_at": now,
            "updated_at": now,
            "provisioning_device_id": provisioning_device_id,
            "provisioning_session_revoked_at": provisioning_session_revoked_at,
            "completed_at": completed_at,
            "failure_code": failure_code,
        },
    )


def test_migration_created_only_approved_columns_constraints_and_indexes(
    postgres_engine: Engine,
) -> None:
    inspector = inspect(postgres_engine)

    assert {column["name"] for column in inspector.get_columns("registration_attempts")} == {
        "id",
        "invitation_id",
        "matrix_user_id",
        "role",
        "status",
        "created_at",
        "updated_at",
        "provisioning_device_id",
        "provisioning_session_revoked_at",
        "completed_at",
        "failure_code",
    }
    constraint_names = {
        constraint["name"]
        for constraint in inspector.get_check_constraints("registration_attempts")
    }
    assert {
        "ck_registration_attempts_provisioning_device_required",
        "ck_registration_attempts_provisioning_revocation_metadata",
        "ck_registration_attempts_provisioning_revocation_required",
        "ck_registration_attempts_unprovisioned_states",
    } <= constraint_names
    assert {index["name"] for index in inspector.get_indexes("registration_attempts")} == {
        "ix_registration_attempts_status_updated_at",
        "uq_registration_attempts_active_invitation_id",
        "uq_registration_attempts_active_matrix_user_id",
    }


def test_partial_indexes_serialize_active_attempts_and_allow_released_retry(
    connection: Connection,
) -> None:
    insert_invitation(connection, INVITATION_ONE, "a")
    insert_invitation(connection, INVITATION_TWO, "b")
    insert_attempt(
        connection,
        attempt_id=ATTEMPT_ONE,
        invitation_id=INVITATION_ONE,
        matrix_user_id="@alice:localhost",
    )

    with pytest.raises(IntegrityError), connection.begin_nested():
        insert_attempt(
            connection,
            attempt_id=ATTEMPT_TWO,
            invitation_id=INVITATION_ONE,
            matrix_user_id="@bob:localhost",
        )

    with pytest.raises(IntegrityError), connection.begin_nested():
        insert_attempt(
            connection,
            attempt_id=ATTEMPT_TWO,
            invitation_id=INVITATION_TWO,
            matrix_user_id="@alice:localhost",
        )

    connection.execute(
        text(
            """
            UPDATE registration_attempts
            SET status = 'released', failure_code = 'username_unavailable'
            WHERE id = :id
            """
        ),
        {"id": ATTEMPT_ONE},
    )
    insert_attempt(
        connection,
        attempt_id=ATTEMPT_THREE,
        invitation_id=INVITATION_ONE,
        matrix_user_id="@alice:localhost",
    )


@pytest.mark.parametrize(
    ("status", "completed_at", "failure_code"),
    [
        ("completed", None, None),
        ("completed", datetime(2026, 7, 23, 11, tzinfo=UTC), None),
        ("released", None, None),
        ("processing", None, "unexpected_failure"),
        ("reconciliation_required", None, "contains space"),
    ],
)
def test_state_constraints_reject_inconsistent_metadata(
    connection: Connection,
    status: str,
    completed_at: datetime | None,
    failure_code: str | None,
) -> None:
    insert_invitation(connection, INVITATION_ONE, "a")

    with pytest.raises(IntegrityError), connection.begin_nested():
        insert_attempt(
            connection,
            attempt_id=ATTEMPT_ONE,
            invitation_id=INVITATION_ONE,
            matrix_user_id="@alice:localhost",
            status=status,
            completed_at=completed_at,
            failure_code=failure_code,
        )


@pytest.mark.parametrize(
    (
        "status",
        "provisioning_device_id",
        "provisioning_session_revoked_at",
        "completed_at",
        "failure_code",
    ),
    [
        ("synapse_created", None, None, None, None),
        (
            "completed",
            "PROVISIONING",
            None,
            datetime(2026, 7, 23, 13, tzinfo=UTC),
            None,
        ),
        (
            "processing",
            "PROVISIONING",
            None,
            None,
            None,
        ),
        (
            "released",
            None,
            datetime(2026, 7, 23, 13, tzinfo=UTC),
            None,
            "username_unavailable",
        ),
        (
            "reconciliation_required",
            "PROVISIONING",
            datetime(2026, 7, 23, 13, tzinfo=UTC),
            None,
            "synapse_result_ambiguous",
        ),
        (
            "synapse_created",
            "PROVISIONING",
            datetime(2026, 7, 23, 11, tzinfo=UTC),
            None,
            None,
        ),
    ],
)
def test_provisioning_constraints_reject_missing_or_inconsistent_evidence(
    connection: Connection,
    status: str,
    provisioning_device_id: str | None,
    provisioning_session_revoked_at: datetime | None,
    completed_at: datetime | None,
    failure_code: str | None,
) -> None:
    insert_invitation(connection, INVITATION_ONE, "a")

    with pytest.raises(IntegrityError), connection.begin_nested():
        insert_attempt(
            connection,
            attempt_id=ATTEMPT_ONE,
            invitation_id=INVITATION_ONE,
            matrix_user_id="@alice:localhost",
            status=status,
            provisioning_device_id=provisioning_device_id,
            provisioning_session_revoked_at=provisioning_session_revoked_at,
            completed_at=completed_at,
            failure_code=failure_code,
        )


def test_completed_attempt_accepts_only_complete_revocation_evidence(
    connection: Connection,
) -> None:
    insert_invitation(connection, INVITATION_ONE, "a")
    revoked_at = datetime(2026, 7, 23, 13, tzinfo=UTC)

    insert_attempt(
        connection,
        attempt_id=ATTEMPT_ONE,
        invitation_id=INVITATION_ONE,
        matrix_user_id="@alice:localhost",
        status="completed",
        provisioning_device_id="PROVISIONING",
        provisioning_session_revoked_at=revoked_at,
        completed_at=revoked_at,
    )


def test_foreign_key_rejects_attempt_without_invitation(connection: Connection) -> None:
    with pytest.raises(IntegrityError), connection.begin_nested():
        insert_attempt(
            connection,
            attempt_id=ATTEMPT_ONE,
            invitation_id=MISSING_INVITATION,
            matrix_user_id="@alice:localhost",
        )


def test_repository_persists_and_completes_attempt_in_order(
    connection: Connection,
) -> None:
    insert_invitation(connection, INVITATION_ONE, "a")
    created_at = datetime(2026, 7, 23, 12, tzinfo=UTC)
    synapse_created_at = created_at + timedelta(minutes=1)
    completed_at = created_at + timedelta(minutes=2)

    with Session(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    ) as session:
        repository = RegistrationAttemptRepository(session)
        attempt = RegistrationAttempt(
            id=ATTEMPT_ONE,
            invitation_id=INVITATION_ONE,
            matrix_user_id="@alice:localhost",
            role=InvitationRole.user,
            status=RegistrationAttemptStatus.processing,
            created_at=created_at,
            updated_at=created_at,
        )

        assert repository.add(attempt) is attempt
        assert repository.get(ATTEMPT_ONE) is attempt
        assert repository.get_active_by_invitation(INVITATION_ONE) is attempt
        assert repository.get_active_by_matrix_user_id("@alice:localhost") is attempt

        created = repository.mark_synapse_created(
            ATTEMPT_ONE,
            provisioning_device_id="PROVISIONING",
            now=synapse_created_at,
        )
        assert created is attempt
        assert created.status is RegistrationAttemptStatus.synapse_created
        assert created.provisioning_device_id == "PROVISIONING"
        assert created.provisioning_session_revoked_at is None
        assert created.updated_at == synapse_created_at
        assert created.failure_code is None
        assert (
            repository.mark_synapse_created(
                ATTEMPT_ONE,
                provisioning_device_id="OTHER",
                now=completed_at,
            )
            is None
        )

        assert repository.mark_completed(ATTEMPT_ONE, completed_at) is None
        revoked = repository.mark_provisioning_session_revoked(
            ATTEMPT_ONE,
            provisioning_device_id="PROVISIONING",
            now=completed_at,
        )
        assert revoked is attempt
        assert revoked.status is RegistrationAttemptStatus.synapse_created
        assert revoked.provisioning_session_revoked_at == completed_at

        finalized_at = completed_at + timedelta(minutes=1)
        completed = repository.mark_completed(ATTEMPT_ONE, finalized_at)
        assert completed is attempt
        assert completed.status is RegistrationAttemptStatus.completed
        assert completed.updated_at == finalized_at
        assert completed.completed_at == finalized_at
        assert completed.failure_code is None
        assert repository.get_active_by_invitation(INVITATION_ONE) is None
        assert repository.get_active_by_matrix_user_id("@alice:localhost") is None
        assert repository.mark_completed(ATTEMPT_ONE, finalized_at) is None


def test_repository_releases_only_processing_attempt(
    connection: Connection,
) -> None:
    insert_invitation(connection, INVITATION_ONE, "a")
    created_at = datetime(2026, 7, 23, 12, tzinfo=UTC)
    released_at = created_at + timedelta(minutes=1)

    with Session(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    ) as session:
        repository = RegistrationAttemptRepository(session)
        repository.add(
            RegistrationAttempt(
                id=ATTEMPT_ONE,
                invitation_id=INVITATION_ONE,
                matrix_user_id="@alice:localhost",
                role=InvitationRole.user,
                status=RegistrationAttemptStatus.processing,
                created_at=created_at,
                updated_at=created_at,
            )
        )

        released = repository.mark_released(
            ATTEMPT_ONE,
            failure_code="username_unavailable",
            now=released_at,
        )
        assert released is not None
        assert released.status is RegistrationAttemptStatus.released
        assert released.updated_at == released_at
        assert released.completed_at is None
        assert released.failure_code == "username_unavailable"
        assert repository.get_active_by_invitation(INVITATION_ONE) is None
        assert (
            repository.mark_reconciliation_required(
                ATTEMPT_ONE,
                failure_code="synapse_result_ambiguous",
                now=released_at,
            )
            is None
        )


@pytest.mark.parametrize(
    "initial_status",
    [
        RegistrationAttemptStatus.processing,
        RegistrationAttemptStatus.synapse_created,
    ],
)
def test_repository_marks_ambiguous_active_attempt_for_reconciliation(
    connection: Connection,
    initial_status: RegistrationAttemptStatus,
) -> None:
    insert_invitation(connection, INVITATION_ONE, "a")
    created_at = datetime(2026, 7, 23, 12, tzinfo=UTC)
    failed_at = created_at + timedelta(minutes=1)

    with Session(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    ) as session:
        repository = RegistrationAttemptRepository(session)
        repository.add(
            RegistrationAttempt(
                id=ATTEMPT_ONE,
                invitation_id=INVITATION_ONE,
                matrix_user_id="@alice:localhost",
                role=InvitationRole.user,
                status=initial_status,
                created_at=created_at,
                updated_at=created_at,
                provisioning_device_id=(
                    "PROVISIONING"
                    if initial_status is RegistrationAttemptStatus.synapse_created
                    else None
                ),
            )
        )

        ambiguous = repository.mark_reconciliation_required(
            ATTEMPT_ONE,
            failure_code="synapse_result_ambiguous",
            now=failed_at,
        )
        assert ambiguous is not None
        assert ambiguous.status is RegistrationAttemptStatus.reconciliation_required
        assert ambiguous.updated_at == failed_at
        assert ambiguous.completed_at is None
        assert ambiguous.provisioning_session_revoked_at is None
        assert ambiguous.failure_code == "synapse_result_ambiguous"
        assert repository.get_active_by_invitation(INVITATION_ONE) is ambiguous
        assert repository.mark_completed(ATTEMPT_ONE, failed_at) is None


def test_repository_recovers_reconciliation_atomically_after_revocation(
    connection: Connection,
) -> None:
    insert_invitation(connection, INVITATION_ONE, "a")
    created_at = datetime(2026, 7, 23, 12, tzinfo=UTC)
    revoked_at = created_at + timedelta(minutes=1)

    with Session(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    ) as session:
        repository = RegistrationAttemptRepository(session)
        attempt = repository.add(
            RegistrationAttempt(
                id=ATTEMPT_ONE,
                invitation_id=INVITATION_ONE,
                matrix_user_id="@alice:localhost",
                role=InvitationRole.user,
                status=RegistrationAttemptStatus.reconciliation_required,
                created_at=created_at,
                updated_at=created_at,
                provisioning_device_id="PROVISIONING",
                failure_code="revocation_result_ambiguous",
            )
        )

        assert (
            repository.mark_provisioning_session_revoked(
                ATTEMPT_ONE,
                provisioning_device_id="OTHER",
                now=revoked_at,
            )
            is None
        )

        recovered = repository.mark_provisioning_session_revoked(
            ATTEMPT_ONE,
            provisioning_device_id="PROVISIONING",
            now=revoked_at,
        )
        assert recovered is attempt
        assert recovered.status is RegistrationAttemptStatus.synapse_created
        assert recovered.provisioning_device_id == "PROVISIONING"
        assert recovered.provisioning_session_revoked_at == revoked_at
        assert recovered.failure_code is None
        assert recovered.updated_at == revoked_at
