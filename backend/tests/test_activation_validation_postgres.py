"""Pré-validação real com convite e limitador no PostgreSQL descartável."""

import os
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import Engine, create_engine, delete, func, select
from sqlalchemy.orm import Session

from social_internal_backend.activations import (
    ActivationValidationRateLimitedError,
    ActivationValidationService,
)
from social_internal_backend.invitations.tokens import hash_invitation_token
from social_internal_backend.models import (
    ActivationRateLimit,
    Invitation,
    InvitationRole,
    InvitationStatus,
    RegistrationAttempt,
)
from social_internal_backend.synapse import SynapseUserNotFoundError

pytestmark = pytest.mark.postgres

NOW = datetime(2026, 7, 27, 12, 5, tzinfo=UTC)
OPAQUE_INVITATION_VALUE = "opaque-postgres-activation-value"


class MissingSynapseIdentity:
    """Simula somente a resposta de conta ausente sem conexão externa."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def get_user(self, user_id: str) -> object:
        self.calls.append(user_id)
        raise SynapseUserNotFoundError


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


def test_prevalidation_counts_atomically_without_mutating_invitation(
    postgres_engine: Engine,
) -> None:
    invitation_id = uuid4()
    token_hash = hash_invitation_token(OPAQUE_INVITATION_VALUE)
    identity = MissingSynapseIdentity()

    try:
        with Session(postgres_engine, expire_on_commit=False) as session:
            invitation = Invitation(
                id=invitation_id,
                token_hash=token_hash,
                role=InvitationRole.user,
                status=InvitationStatus.pending,
                created_by="@admin:localhost",
                target_user_id="@employee:localhost",
                created_at=NOW,
                expires_at=NOW + timedelta(hours=24),
            )
            session.add(invitation)
            session.commit()

            service = ActivationValidationService(
                session,
                identity_provider=identity,
                matrix_server_name="localhost",
                clock=lambda: NOW,
            )
            for _ in range(10):
                result = service.validate(OPAQUE_INVITATION_VALUE)
                assert result.target_user_id == "@employee:localhost"

            with pytest.raises(ActivationValidationRateLimitedError):
                service.validate(OPAQUE_INVITATION_VALUE)

            session.expire_all()
            stored_invitation = session.get(Invitation, invitation_id)
            stored_count = session.scalar(
                select(ActivationRateLimit.attempt_count).where(
                    ActivationRateLimit.invitation_token_hash == token_hash
                )
            )
            attempt_count = session.scalar(
                select(func.count())
                .select_from(RegistrationAttempt)
                .where(RegistrationAttempt.invitation_id == invitation_id)
            )

            assert stored_invitation is not None
            assert stored_invitation.status is InvitationStatus.pending
            assert stored_invitation.used_at is None
            assert stored_invitation.revoked_at is None
            assert stored_count == 11
            assert attempt_count == 0
            assert identity.calls == ["@employee:localhost"] * 10
    finally:
        with postgres_engine.begin() as connection:
            connection.execute(
                delete(ActivationRateLimit).where(
                    ActivationRateLimit.invitation_token_hash == token_hash
                )
            )
            connection.execute(delete(Invitation).where(Invitation.id == invitation_id))
