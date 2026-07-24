"""Transações compostas do cadastro em PostgreSQL real."""

import os
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import Connection, Engine, create_engine, text
from sqlalchemy.orm import Session

from social_internal_backend.models import RegistrationAttemptStatus
from social_internal_backend.registrations import (
    RegistrationCheckpointConflictError,
    RegistrationFinalizationConflictError,
    RegistrationReservationConflictError,
    RegistrationUnitOfWork,
)

pytestmark = pytest.mark.postgres

INVITATION_ONE = UUID("50000000-0000-0000-0000-000000000001")
INVITATION_TWO = UUID("50000000-0000-0000-0000-000000000002")
ATTEMPT_ONE = UUID("60000000-0000-0000-0000-000000000001")
TARGET_USER_ID = "@alice:localhost"
DEVICE_ID = "PROVISIONING"
NOW = datetime(2026, 7, 24, 15, tzinfo=UTC)


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


def insert_invitation(
    connection: Connection,
    *,
    invitation_id: UUID,
    digest_marker: str,
    status: str = "pending",
    target_user_id: str = TARGET_USER_ID,
    role: str = "user",
) -> None:
    """Cria o convite mínimo com identidade previamente definida."""

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
                expires_at,
                used_at,
                accepted_user_id
            )
            VALUES (
                :id,
                :token_hash,
                CAST(:role AS VARCHAR),
                CAST(:status AS VARCHAR),
                '@admin:localhost',
                CAST(:target_user_id AS VARCHAR),
                :created_at,
                :expires_at,
                CASE
                    WHEN CAST(:status AS VARCHAR) = 'used'
                    THEN :created_at
                    ELSE NULL
                END,
                CASE
                    WHEN CAST(:status AS VARCHAR) = 'used'
                    THEN CAST(:target_user_id AS VARCHAR)
                    ELSE NULL
                END
            )
            """
        ),
        {
            "id": invitation_id,
            "token_hash": digest_marker * 64,
            "role": role,
            "status": status,
            "target_user_id": target_user_id,
            "created_at": NOW - timedelta(hours=1),
            "expires_at": NOW + timedelta(hours=23),
        },
    )


def insert_processing_attempt(
    connection: Connection,
    *,
    attempt_id: UUID,
    invitation_id: UUID,
    matrix_user_id: str = TARGET_USER_ID,
) -> None:
    """Cria uma tentativa ativa para provocar concorrência real."""

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
                updated_at
            )
            VALUES (
                :id,
                :invitation_id,
                :matrix_user_id,
                'user',
                'processing',
                :created_at,
                :updated_at
            )
            """
        ),
        {
            "id": attempt_id,
            "invitation_id": invitation_id,
            "matrix_user_id": matrix_user_id,
            "created_at": NOW - timedelta(minutes=2),
            "updated_at": NOW - timedelta(minutes=2),
        },
    )


def make_session(connection: Connection) -> Session:
    """Cria uma sessão cujo commit permanece dentro do teste isolado."""

    return Session(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )


def test_reservation_persists_invitation_and_derived_identity_together(
    connection: Connection,
) -> None:
    insert_invitation(
        connection,
        invitation_id=INVITATION_ONE,
        digest_marker="a",
        role="group_admin",
    )

    with make_session(connection) as session:
        reservation = RegistrationUnitOfWork(session).reserve(
            token_hash="a" * 64,
            now=NOW,
        )
        assert reservation.invitation.id == INVITATION_ONE
        assert reservation.attempt.matrix_user_id == TARGET_USER_ID
        assert reservation.attempt.role.value == "group_admin"

    persisted = (
        connection.execute(
            text(
                """
                SELECT i.status AS invitation_status,
                       a.matrix_user_id,
                       a.role,
                       a.status AS attempt_status
                FROM invitations AS i
                JOIN registration_attempts AS a ON a.invitation_id = i.id
                WHERE i.id = :id
                """
            ),
            {"id": INVITATION_ONE},
        )
        .mappings()
        .one()
    )
    assert persisted == {
        "invitation_status": "processing",
        "matrix_user_id": TARGET_USER_ID,
        "role": "group_admin",
        "attempt_status": "processing",
    }


def test_reservation_rolls_back_claim_when_active_identity_conflicts(
    connection: Connection,
) -> None:
    insert_invitation(
        connection,
        invitation_id=INVITATION_ONE,
        digest_marker="a",
        status="used",
    )
    insert_processing_attempt(
        connection,
        attempt_id=ATTEMPT_ONE,
        invitation_id=INVITATION_ONE,
    )
    insert_invitation(
        connection,
        invitation_id=INVITATION_TWO,
        digest_marker="b",
    )

    with (
        make_session(connection) as session,
        pytest.raises(RegistrationReservationConflictError),
    ):
        RegistrationUnitOfWork(session).reserve(
            token_hash="b" * 64,
            now=NOW,
        )

    invitation_status = connection.execute(
        text("SELECT status FROM invitations WHERE id = :id"),
        {"id": INVITATION_TWO},
    ).scalar_one()
    attempt_count = connection.execute(
        text(
            """
            SELECT count(*)
            FROM registration_attempts
            WHERE invitation_id = :invitation_id
            """
        ),
        {"invitation_id": INVITATION_TWO},
    ).scalar_one()
    assert invitation_status == "pending"
    assert attempt_count == 0


def test_release_closes_attempt_and_returns_invitation_in_one_commit(
    connection: Connection,
) -> None:
    insert_invitation(
        connection,
        invitation_id=INVITATION_ONE,
        digest_marker="a",
    )

    with make_session(connection) as session:
        unit_of_work = RegistrationUnitOfWork(session)
        reservation = unit_of_work.reserve(token_hash="a" * 64, now=NOW)
        released = unit_of_work.release(
            attempt_id=reservation.attempt.id,
            failure_code="creation_not_started",
            now=NOW + timedelta(minutes=1),
        )
        assert released.invitation.status.value == "pending"
        assert released.attempt.status is RegistrationAttemptStatus.released

    persisted = (
        connection.execute(
            text(
                """
                SELECT i.status AS invitation_status,
                       a.status AS attempt_status,
                       a.failure_code
                FROM invitations AS i
                JOIN registration_attempts AS a ON a.invitation_id = i.id
                WHERE i.id = :id
                """
            ),
            {"id": INVITATION_ONE},
        )
        .mappings()
        .one()
    )
    assert persisted == {
        "invitation_status": "pending",
        "attempt_status": "released",
        "failure_code": "creation_not_started",
    }


def test_reconciliation_revocation_and_finalization_follow_durable_order(
    connection: Connection,
) -> None:
    insert_invitation(
        connection,
        invitation_id=INVITATION_ONE,
        digest_marker="a",
        role="group_admin",
    )

    with make_session(connection) as session:
        unit_of_work = RegistrationUnitOfWork(session)
        reservation = unit_of_work.reserve(token_hash="a" * 64, now=NOW)
        created = unit_of_work.record_synapse_created(
            attempt_id=reservation.attempt.id,
            provisioning_device_id=DEVICE_ID,
            now=NOW + timedelta(minutes=1),
        )
        assert created.status is RegistrationAttemptStatus.synapse_created

        with pytest.raises(RegistrationFinalizationConflictError):
            unit_of_work.finalize(
                attempt_id=reservation.attempt.id,
                now=NOW + timedelta(minutes=2),
            )

        ambiguous = unit_of_work.record_reconciliation_required(
            attempt_id=reservation.attempt.id,
            failure_code="revocation_result_ambiguous",
            now=NOW + timedelta(minutes=2),
        )
        assert ambiguous.status is RegistrationAttemptStatus.reconciliation_required

        with pytest.raises(RegistrationCheckpointConflictError):
            unit_of_work.record_provisioning_session_revoked(
                attempt_id=reservation.attempt.id,
                provisioning_device_id="OTHER",
                now=NOW + timedelta(minutes=3),
            )

        recovered = unit_of_work.record_provisioning_session_revoked(
            attempt_id=reservation.attempt.id,
            provisioning_device_id=DEVICE_ID,
            now=NOW + timedelta(minutes=3),
        )
        assert recovered.status is RegistrationAttemptStatus.synapse_created
        assert recovered.failure_code is None

        finalization = unit_of_work.finalize(
            attempt_id=reservation.attempt.id,
            now=NOW + timedelta(minutes=4),
        )
        assert finalization.invitation.status.value == "used"
        assert finalization.attempt.status is RegistrationAttemptStatus.completed
        assert finalization.role_assignment.role.value == "group_admin"

    persisted = (
        connection.execute(
            text(
                """
                SELECT i.status AS invitation_status,
                       i.accepted_user_id,
                       a.status AS attempt_status,
                       a.provisioning_device_id,
                       a.provisioning_session_revoked_at,
                       a.completed_at,
                       a.failure_code,
                       r.role,
                       r.granted_by
                FROM invitations AS i
                JOIN registration_attempts AS a ON a.invitation_id = i.id
                JOIN user_role_assignments AS r
                  ON r.matrix_user_id = a.matrix_user_id
                WHERE i.id = :id
                """
            ),
            {"id": INVITATION_ONE},
        )
        .mappings()
        .one()
    )
    assert persisted["invitation_status"] == "used"
    assert persisted["accepted_user_id"] == TARGET_USER_ID
    assert persisted["attempt_status"] == "completed"
    assert persisted["provisioning_device_id"] == DEVICE_ID
    assert persisted["provisioning_session_revoked_at"] == NOW + timedelta(minutes=3)
    assert persisted["completed_at"] == NOW + timedelta(minutes=4)
    assert persisted["failure_code"] is None
    assert persisted["role"] == "group_admin"
    assert persisted["granted_by"] == "@admin:localhost"


def test_finalization_rolls_back_invitation_and_attempt_when_role_conflicts(
    connection: Connection,
) -> None:
    insert_invitation(
        connection,
        invitation_id=INVITATION_ONE,
        digest_marker="a",
    )
    with make_session(connection) as session:
        unit_of_work = RegistrationUnitOfWork(session)
        reservation = unit_of_work.reserve(token_hash="a" * 64, now=NOW)
        unit_of_work.record_synapse_created(
            attempt_id=reservation.attempt.id,
            provisioning_device_id=DEVICE_ID,
            now=NOW + timedelta(minutes=1),
        )
        unit_of_work.record_provisioning_session_revoked(
            attempt_id=reservation.attempt.id,
            provisioning_device_id=DEVICE_ID,
            now=NOW + timedelta(minutes=2),
        )

    connection.execute(
        text(
            """
            INSERT INTO user_role_assignments (
                matrix_user_id,
                role,
                granted_at,
                granted_by
            )
            VALUES (
                :matrix_user_id,
                'group_admin',
                :granted_at,
                '@admin:localhost'
            )
            """
        ),
        {
            "matrix_user_id": TARGET_USER_ID,
            "granted_at": NOW,
        },
    )

    with (
        make_session(connection) as session,
        pytest.raises(RegistrationFinalizationConflictError),
    ):
        RegistrationUnitOfWork(session).finalize(
            attempt_id=reservation.attempt.id,
            now=NOW + timedelta(minutes=3),
        )

    persisted = (
        connection.execute(
            text(
                """
                SELECT i.status AS invitation_status,
                       i.accepted_user_id,
                       a.status AS attempt_status,
                       a.completed_at,
                       r.role
                FROM invitations AS i
                JOIN registration_attempts AS a ON a.invitation_id = i.id
                JOIN user_role_assignments AS r
                  ON r.matrix_user_id = a.matrix_user_id
                WHERE i.id = :id
                """
            ),
            {"id": INVITATION_ONE},
        )
        .mappings()
        .one()
    )
    assert persisted == {
        "invitation_status": "processing",
        "accepted_user_id": None,
        "attempt_status": "synapse_created",
        "completed_at": None,
        "role": "group_admin",
    }
