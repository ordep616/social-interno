"""Regras de negócio e transações do serviço de convites."""

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import cast
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from social_internal_backend.invitations.service import (
    INVITATION_LIFETIME,
    InvitationConflictError,
    InvitationNotFoundError,
    InvitationService,
    InvitationTransitionError,
    InvitationUnavailableError,
)
from social_internal_backend.invitations.tokens import hash_invitation_token
from social_internal_backend.models import Invitation, InvitationRole, InvitationStatus

NOW = datetime(2026, 7, 22, 12, tzinfo=UTC)
OPAQUE_VALUE = "valor-opaco-de-teste"


def make_invitation(
    *,
    status: InvitationStatus = InvitationStatus.pending,
    expires_at: datetime | None = None,
    accepted_user_id: str | None = None,
) -> Invitation:
    return Invitation(
        id=uuid4(),
        token_hash=hash_invitation_token(OPAQUE_VALUE),
        role=InvitationRole.user,
        status=status,
        created_by="@admin:localhost",
        created_at=NOW,
        expires_at=expires_at or NOW + INVITATION_LIFETIME,
        accepted_user_id=accepted_user_id,
    )


class FakeInvitationRepository:
    """Controla resultados sem depender de PostgreSQL nos testes unitários."""

    def __init__(self) -> None:
        self.added: Invitation | None = None
        self.by_id: Invitation | None = None
        self.by_hash: Invitation | None = None
        self.listed: Sequence[Invitation] = []
        self.claimed: Invitation | None = None
        self.expired: Invitation | None = None
        self.revoked: Invitation | None = None
        self.completed: Invitation | None = None
        self.released: Invitation | None = None
        self.raise_on_add: Exception | None = None

    def add(self, invitation: Invitation) -> Invitation:
        if self.raise_on_add is not None:
            raise self.raise_on_add
        self.added = invitation
        return invitation

    def get(self, invitation_id: UUID) -> Invitation | None:
        del invitation_id
        return self.by_id

    def get_by_token_hash(self, token_hash: str) -> Invitation | None:
        assert token_hash == hash_invitation_token(OPAQUE_VALUE)
        return self.by_hash

    def list(self, *, offset: int = 0, limit: int = 100) -> Sequence[Invitation]:
        assert offset >= 0
        assert limit >= 1
        return self.listed

    def claim_pending(self, token_hash: str, now: datetime) -> Invitation | None:
        assert token_hash == hash_invitation_token(OPAQUE_VALUE)
        assert now == NOW
        return self.claimed

    def expire_pending(self, token_hash: str, now: datetime) -> Invitation | None:
        assert token_hash == hash_invitation_token(OPAQUE_VALUE)
        assert now == NOW
        return self.expired

    def revoke_pending(self, invitation_id: UUID, now: datetime) -> Invitation | None:
        del invitation_id
        assert now == NOW
        return self.revoked

    def complete_processing(
        self,
        invitation_id: UUID,
        accepted_user_id: str,
        now: datetime,
    ) -> Invitation | None:
        del invitation_id
        assert accepted_user_id == "@user:localhost"
        assert now == NOW
        return self.completed

    def release_processing(self, invitation_id: UUID, now: datetime) -> Invitation | None:
        del invitation_id
        assert now == NOW
        return self.released


def make_service(
    repository: FakeInvitationRepository,
    session: MagicMock,
    *,
    now: datetime = NOW,
) -> InvitationService:
    return InvitationService(
        session,
        repository=repository,
        clock=lambda: now,
        token_factory=lambda: OPAQUE_VALUE,
    )


def test_issues_24_hour_invitation_and_commits_without_exposing_token_in_repr() -> None:
    repository = FakeInvitationRepository()
    session = MagicMock(spec=Session)
    issued = make_service(repository, session).issue(
        role=InvitationRole.group_admin,
        created_by="@admin:localhost",
    )

    assert issued.token == OPAQUE_VALUE
    assert OPAQUE_VALUE not in repr(issued)
    assert issued.invitation is repository.added
    assert issued.invitation.token_hash == hash_invitation_token(OPAQUE_VALUE)
    assert issued.invitation.role is InvitationRole.group_admin
    assert issued.invitation.expires_at - issued.invitation.created_at == timedelta(hours=24)
    session.commit.assert_called_once_with()


def test_issue_rejects_empty_actor_and_rolls_back_database_failure() -> None:
    repository = FakeInvitationRepository()
    session = MagicMock(spec=Session)
    service = make_service(repository, session)

    with pytest.raises(ValueError, match="created_by"):
        service.issue(role=InvitationRole.user, created_by=" ")

    with pytest.raises(ValueError, match="role"):
        service.issue(
            role=cast(InvitationRole, "platform_admin"),
            created_by="@admin:localhost",
        )

    repository.raise_on_add = RuntimeError("database failed")
    with pytest.raises(RuntimeError, match="database failed"):
        service.issue(role=InvitationRole.user, created_by="@admin:localhost")
    session.rollback.assert_called_once_with()


def test_get_and_list_apply_not_found_and_pagination_rules() -> None:
    repository = FakeInvitationRepository()
    session = MagicMock(spec=Session)
    service = make_service(repository, session)
    invitation = make_invitation()
    repository.by_id = invitation
    repository.listed = [invitation]

    assert service.get(invitation.id) is invitation
    assert service.list(offset=0, limit=100) == [invitation]

    repository.by_id = None
    with pytest.raises(InvitationNotFoundError):
        service.get(invitation.id)
    with pytest.raises(ValueError, match="offset"):
        service.list(offset=-1)
    with pytest.raises(ValueError, match="limit"):
        service.list(limit=0)
    with pytest.raises(ValueError, match="limit"):
        service.list(limit=101)


def test_validate_accepts_only_pending_unexpired_invitation() -> None:
    repository = FakeInvitationRepository()
    session = MagicMock(spec=Session)
    service = make_service(repository, session)
    invitation = make_invitation()
    repository.by_hash = invitation

    assert service.validate(OPAQUE_VALUE) is invitation

    repository.by_hash = None
    with pytest.raises(InvitationNotFoundError):
        service.validate(OPAQUE_VALUE)

    repository.by_hash = make_invitation(status=InvitationStatus.revoked)
    with pytest.raises(InvitationUnavailableError):
        service.validate(OPAQUE_VALUE)

    repository.by_hash = make_invitation(expires_at=NOW)
    with pytest.raises(InvitationUnavailableError):
        service.validate(OPAQUE_VALUE)


def test_revoke_is_atomic_idempotent_and_rejects_conflicting_state() -> None:
    repository = FakeInvitationRepository()
    session = MagicMock(spec=Session)
    service = make_service(repository, session)
    invitation = make_invitation(status=InvitationStatus.revoked)

    repository.revoked = invitation
    assert service.revoke(invitation.id) is invitation
    session.commit.assert_called_once_with()

    repository.revoked = None
    repository.by_id = invitation
    assert service.revoke(invitation.id) is invitation

    repository.by_id = make_invitation(status=InvitationStatus.processing)
    with pytest.raises(InvitationConflictError):
        service.revoke(invitation.id)

    repository.by_id = None
    with pytest.raises(InvitationNotFoundError):
        service.revoke(invitation.id)


def test_begin_processing_claims_once_and_classifies_failures() -> None:
    repository = FakeInvitationRepository()
    session = MagicMock(spec=Session)
    service = make_service(repository, session)
    processing = make_invitation(status=InvitationStatus.processing)

    repository.claimed = processing
    assert service.begin_processing(OPAQUE_VALUE) is processing

    repository.claimed = None
    repository.expired = make_invitation(status=InvitationStatus.expired)
    with pytest.raises(InvitationUnavailableError):
        service.begin_processing(OPAQUE_VALUE)

    repository.expired = None
    repository.by_hash = make_invitation(status=InvitationStatus.used)
    with pytest.raises(InvitationUnavailableError):
        service.begin_processing(OPAQUE_VALUE)

    repository.by_hash = None
    with pytest.raises(InvitationNotFoundError):
        service.begin_processing(OPAQUE_VALUE)


def test_complete_is_atomic_idempotent_for_same_user_and_validates_input() -> None:
    repository = FakeInvitationRepository()
    session = MagicMock(spec=Session)
    service = make_service(repository, session)
    used = make_invitation(
        status=InvitationStatus.used,
        accepted_user_id="@user:localhost",
    )

    repository.completed = used
    assert service.complete(used.id, accepted_user_id="@user:localhost") is used

    repository.completed = None
    repository.by_id = used
    assert service.complete(used.id, accepted_user_id="@user:localhost") is used

    repository.by_id = make_invitation(status=InvitationStatus.pending)
    with pytest.raises(InvitationTransitionError):
        service.complete(used.id, accepted_user_id="@user:localhost")

    repository.by_id = None
    with pytest.raises(InvitationNotFoundError):
        service.complete(used.id, accepted_user_id="@user:localhost")

    with pytest.raises(ValueError, match="accepted_user_id"):
        service.complete(used.id, accepted_user_id=" ")


def test_release_commits_transition_and_rejects_missing_or_wrong_state() -> None:
    repository = FakeInvitationRepository()
    session = MagicMock(spec=Session)
    service = make_service(repository, session)
    pending = make_invitation()

    repository.released = pending
    assert service.release(pending.id) is pending

    repository.released = None
    repository.by_id = make_invitation(status=InvitationStatus.used)
    with pytest.raises(InvitationTransitionError):
        service.release(pending.id)

    repository.by_id = None
    with pytest.raises(InvitationNotFoundError):
        service.release(pending.id)


def test_rejects_naive_clock() -> None:
    repository = FakeInvitationRepository()
    session = MagicMock(spec=Session)
    service = make_service(repository, session, now=datetime(2026, 7, 22, 12))

    with pytest.raises(ValueError, match="timezone-aware"):
        service.issue(role=InvitationRole.user, created_by="@admin:localhost")
