"""Restrições reais da identidade previamente definida dos convites."""

import os
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import Connection, Engine, create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from social_internal_backend.invitations import InvitationService
from social_internal_backend.models import Invitation, InvitationRole
from social_internal_backend.synapse import SynapseUserNotFoundError

pytestmark = pytest.mark.postgres

INVITATION_ONE = UUID("30000000-0000-0000-0000-000000000001")
INVITATION_TWO = UUID("30000000-0000-0000-0000-000000000002")
INVITATION_THREE = UUID("30000000-0000-0000-0000-000000000003")


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
    status: str,
    target_user_id: str | None,
) -> None:
    """Insere diretamente para o PostgreSQL validar o contrato."""

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
                expires_at,
                used_at,
                accepted_user_id,
                revoked_at
            )
            VALUES (
                :id,
                :token_hash,
                'user',
                CAST(:status AS VARCHAR),
                '@admin:localhost',
                CAST(:target_user_id AS VARCHAR),
                :created_at,
                :expires_at,
                CASE
                    WHEN CAST(:status AS VARCHAR) = 'used' THEN :created_at
                    ELSE NULL
                END,
                CASE
                    WHEN CAST(:status AS VARCHAR) = 'used'
                    THEN '@accepted:localhost'
                    ELSE NULL
                END,
                CASE
                    WHEN CAST(:status AS VARCHAR) = 'revoked' THEN :created_at
                    ELSE NULL
                END
            )
            """
        ),
        {
            "id": invitation_id,
            "token_hash": digest_marker * 64,
            "status": status,
            "target_user_id": target_user_id,
            "created_at": now,
            "expires_at": now + timedelta(hours=24),
        },
    )


class MissingSynapseUserLookup:
    """Confirma disponibilidade sem realizar chamada externa no teste do banco."""

    def get_user(self, user_id: str) -> object:
        del user_id
        raise SynapseUserNotFoundError


def test_migration_created_target_identity_contract(postgres_engine: Engine) -> None:
    inspector = inspect(postgres_engine)
    columns = {column["name"] for column in inspector.get_columns("invitations")}
    constraints = {
        constraint["name"]: constraint["sqltext"]
        for constraint in inspector.get_check_constraints("invitations")
    }
    indexes = {index["name"]: index for index in inspector.get_indexes("invitations")}

    assert "target_user_id" in columns
    assert "conflicted" in constraints["ck_invitations_status"]
    assert "target_user_id" in constraints["ck_invitations_target_user_id_required"]
    assert "target_user_id" in constraints["ck_invitations_target_user_id_format"]
    target_index = indexes["uq_invitations_active_target_user_id"]
    assert target_index["unique"]
    predicate = str(target_index["dialect_options"]["postgresql_where"])
    assert "pending" in predicate
    assert "processing" in predicate
    assert "conflicted" not in predicate


@pytest.mark.parametrize("status", ["pending", "processing", "used", "conflicted"])
def test_non_historical_status_rejects_missing_target_identity(
    connection: Connection,
    status: str,
) -> None:
    with pytest.raises(IntegrityError), connection.begin_nested():
        insert_invitation(
            connection,
            invitation_id=INVITATION_ONE,
            digest_marker="a",
            status=status,
            target_user_id=None,
        )


@pytest.mark.parametrize("status", ["revoked", "expired"])
def test_historical_terminal_status_accepts_missing_target_identity(
    connection: Connection,
    status: str,
) -> None:
    insert_invitation(
        connection,
        invitation_id=INVITATION_ONE,
        digest_marker="a",
        status=status,
        target_user_id=None,
    )


def test_active_target_identity_is_unique_but_terminal_conflict_is_not(
    connection: Connection,
) -> None:
    target_user_id = "@employee:localhost"
    insert_invitation(
        connection,
        invitation_id=INVITATION_ONE,
        digest_marker="a",
        status="pending",
        target_user_id=target_user_id,
    )

    with pytest.raises(IntegrityError), connection.begin_nested():
        insert_invitation(
            connection,
            invitation_id=INVITATION_TWO,
            digest_marker="b",
            status="processing",
            target_user_id=target_user_id,
        )

    insert_invitation(
        connection,
        invitation_id=INVITATION_THREE,
        digest_marker="c",
        status="conflicted",
        target_user_id=target_user_id,
    )


def test_target_identity_requires_matrix_user_id_shape(connection: Connection) -> None:
    with pytest.raises(IntegrityError), connection.begin_nested():
        insert_invitation(
            connection,
            invitation_id=INVITATION_ONE,
            digest_marker="a",
            status="pending",
            target_user_id="employee without domain",
        )


def test_service_issues_invitation_with_predefined_identity(connection: Connection) -> None:
    with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
        issued = InvitationService(
            session,
            identity_provider=MissingSynapseUserLookup(),
            matrix_server_name="localhost",
            clock=lambda: datetime(2026, 7, 23, 12, tzinfo=UTC),
            token_factory=lambda: "opaque-postgres-invitation-token",
        ).issue(
            role=InvitationRole.user,
            created_by="@admin:localhost",
            username="employee",
        )

        persisted = session.get(Invitation, issued.invitation.id)
        assert persisted is not None
        assert persisted.target_user_id == "@employee:localhost"
        assert persisted.role is InvitationRole.user
