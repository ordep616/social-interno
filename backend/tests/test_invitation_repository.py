"""Contrato SQLAlchemy do repositório de convites."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

from sqlalchemy.orm import Session

from social_internal_backend.invitations.repository import InvitationRepository
from social_internal_backend.models import Invitation, InvitationRole, InvitationStatus


def make_invitation(*, status: InvitationStatus = InvitationStatus.pending) -> Invitation:
    now = datetime(2026, 7, 22, 12, tzinfo=UTC)
    return Invitation(
        id=uuid4(),
        token_hash="a" * 64,
        role=InvitationRole.user,
        status=status,
        created_by="@admin:localhost",
        target_user_id="@employee:localhost",
        created_at=now,
        expires_at=now + timedelta(hours=24),
    )


def test_adds_flushes_and_gets_invitation() -> None:
    session = MagicMock(spec=Session)
    repository = InvitationRepository(session)
    invitation = make_invitation()
    session.get.return_value = invitation

    assert repository.add(invitation) is invitation
    assert repository.get(invitation.id) is invitation
    session.add.assert_called_once_with(invitation)
    session.flush.assert_called_once_with()
    session.get.assert_called_once_with(Invitation, invitation.id)


def test_queries_by_hash_active_target_and_lists_with_pagination() -> None:
    session = MagicMock(spec=Session)
    repository = InvitationRepository(session)
    invitation = make_invitation()
    session.scalars.return_value.one_or_none.return_value = invitation
    session.scalars.return_value.all.return_value = [invitation]

    assert repository.get_by_token_hash("a" * 64) is invitation
    assert repository.get_active_by_target_user_id("@employee:localhost") is invitation
    assert repository.list(offset=10, limit=20) == [invitation]
    assert session.scalars.call_count == 3


def test_executes_all_atomic_transitions() -> None:
    session = MagicMock(spec=Session)
    repository = InvitationRepository(session)
    invitation = make_invitation()
    now = datetime(2026, 7, 22, 12, tzinfo=UTC)
    session.execute.return_value.scalar_one_or_none.return_value = invitation

    assert repository.claim_pending("a" * 64, now) is invitation
    assert repository.expire_pending("a" * 64, now) is invitation
    assert repository.revoke_pending(invitation.id, now) is invitation
    assert repository.complete_processing(invitation.id, "@user:localhost", now) is invitation
    assert repository.release_processing(invitation.id, now) is invitation
    assert session.execute.call_count == 5
