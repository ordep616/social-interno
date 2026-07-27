"""Regras de negócio da pré-validação pública."""

from datetime import UTC, datetime, timedelta
from typing import cast
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from social_internal_backend.activations import (
    ActivationValidationConflictError,
    ActivationValidationNotFoundError,
    ActivationValidationRateLimitedError,
    ActivationValidationService,
    ActivationValidationStorageUnavailableError,
    ActivationValidationUnavailableError,
)
from social_internal_backend.invitations.tokens import hash_invitation_token
from social_internal_backend.models import (
    ActivationRateLimitKind,
    Invitation,
    InvitationRole,
    InvitationStatus,
)
from social_internal_backend.rate_limits import ActivationRateLimitDecision
from social_internal_backend.synapse import SynapseAdminUnavailableError, SynapseUserNotFoundError

NOW = datetime(2026, 7, 27, 12, 5, tzinfo=UTC)
OPAQUE_INVITATION_VALUE = "opaque-activation-value"


def make_invitation(
    *,
    status: InvitationStatus = InvitationStatus.pending,
    target_user_id: str | None = "@employee:localhost",
    expires_at: datetime = NOW + timedelta(hours=12),
) -> Invitation:
    return Invitation(
        id=uuid4(),
        token_hash=hash_invitation_token(OPAQUE_INVITATION_VALUE),
        role=InvitationRole.user,
        status=status,
        created_by="@admin:localhost",
        target_user_id=target_user_id,
        created_at=NOW - timedelta(hours=12),
        expires_at=expires_at,
        used_at=None,
        revoked_at=None,
        accepted_user_id=None,
    )


class FakeInvitationRepository:
    def __init__(self, invitation: Invitation | None) -> None:
        self.invitation = invitation
        self.received_hash: str | None = None
        self.error: Exception | None = None

    def get_by_token_hash(self, token_hash: str) -> Invitation | None:
        self.received_hash = token_hash
        if self.error is not None:
            raise self.error
        return self.invitation


class FakeAttemptRepository:
    def __init__(self) -> None:
        self.active_attempt: object | None = None

    def get_active_by_invitation(self, invitation_id: UUID) -> object | None:
        del invitation_id
        return self.active_attempt


class FakeRateLimitRepository:
    def __init__(self) -> None:
        self.decision: ActivationRateLimitDecision | None = ActivationRateLimitDecision(
            allowed=True,
            attempt_count=1,
            limit=10,
            retry_after_seconds=595,
            window_ends_at=NOW + timedelta(minutes=10),
        )
        self.arguments: tuple[ActivationRateLimitKind, str, datetime] | None = None
        self.error: Exception | None = None

    def consume_existing_invitation(
        self,
        *,
        counter_kind: ActivationRateLimitKind,
        invitation_token_hash: str,
        now: datetime,
    ) -> ActivationRateLimitDecision | None:
        self.arguments = (counter_kind, invitation_token_hash, now)
        if self.error is not None:
            raise self.error
        return self.decision


class FakeIdentityProvider:
    def __init__(self, events: list[str] | None = None) -> None:
        self.error: Exception | None = SynapseUserNotFoundError()
        self.requested_user_id: str | None = None
        self.events = events

    def get_user(self, user_id: str) -> object:
        self.requested_user_id = user_id
        if self.events is not None:
            self.events.append("synapse")
        if self.error is not None:
            raise self.error
        return object()


def build_service(
    invitation: Invitation | None,
    *,
    session: MagicMock | None = None,
    events: list[str] | None = None,
) -> tuple[
    ActivationValidationService,
    MagicMock,
    FakeInvitationRepository,
    FakeAttemptRepository,
    FakeRateLimitRepository,
    FakeIdentityProvider,
]:
    resolved_session = session or MagicMock(spec=Session)
    invitations = FakeInvitationRepository(invitation)
    attempts = FakeAttemptRepository()
    limits = FakeRateLimitRepository()
    identity = FakeIdentityProvider(events)
    service = ActivationValidationService(
        resolved_session,
        identity_provider=identity,
        matrix_server_name="localhost",
        invitation_repository=invitations,
        attempt_repository=attempts,
        rate_limit_repository=limits,
        clock=lambda: NOW,
    )
    return service, resolved_session, invitations, attempts, limits, identity


def test_valid_invitation_commits_counter_before_synapse_lookup() -> None:
    events: list[str] = []
    session = MagicMock(spec=Session)
    session.commit.side_effect = lambda: events.append("commit")
    invitation = make_invitation()
    service, _, invitations, _, limits, identity = build_service(
        invitation,
        session=session,
        events=events,
    )

    result = service.validate(OPAQUE_INVITATION_VALUE)

    expected_hash = hash_invitation_token(OPAQUE_INVITATION_VALUE)
    assert result.target_user_id == "@employee:localhost"
    assert result.username == "employee"
    assert result.role is InvitationRole.user
    assert result.expires_at == invitation.expires_at
    assert invitations.received_hash == expected_hash
    assert limits.arguments == (
        ActivationRateLimitKind.activation_validation,
        expected_hash,
        NOW,
    )
    assert identity.requested_user_id == "@employee:localhost"
    assert events == ["commit", "synapse"]
    assert invitation.status is InvitationStatus.pending


def test_unknown_token_creates_no_counter_and_does_not_call_synapse() -> None:
    service, session, _, _, limits, identity = build_service(None)

    with pytest.raises(ActivationValidationNotFoundError):
        service.validate(OPAQUE_INVITATION_VALUE)

    assert limits.arguments is None
    assert identity.requested_user_id is None
    session.rollback.assert_called_once_with()
    session.commit.assert_not_called()


@pytest.mark.parametrize(
    ("status", "expires_at"),
    [
        (InvitationStatus.used, NOW + timedelta(hours=1)),
        (InvitationStatus.revoked, NOW + timedelta(hours=1)),
        (InvitationStatus.expired, NOW + timedelta(hours=1)),
        (InvitationStatus.pending, NOW),
    ],
)
def test_terminal_or_expired_invitation_is_unavailable_after_counting(
    status: InvitationStatus,
    expires_at: datetime,
) -> None:
    service, session, _, _, limits, identity = build_service(
        make_invitation(status=status, expires_at=expires_at)
    )

    with pytest.raises(ActivationValidationUnavailableError):
        service.validate(OPAQUE_INVITATION_VALUE)

    assert limits.arguments is not None
    assert identity.requested_user_id is None
    session.commit.assert_called_once_with()


@pytest.mark.parametrize("status", [InvitationStatus.processing, InvitationStatus.conflicted])
def test_processing_or_conflicted_invitation_is_generic_conflict(
    status: InvitationStatus,
) -> None:
    service, session, _, _, _, identity = build_service(make_invitation(status=status))

    with pytest.raises(ActivationValidationConflictError):
        service.validate(OPAQUE_INVITATION_VALUE)

    assert identity.requested_user_id is None
    session.commit.assert_called_once_with()


def test_active_registration_attempt_is_generic_conflict() -> None:
    service, session, _, attempts, _, identity = build_service(make_invitation())
    attempts.active_attempt = object()

    with pytest.raises(ActivationValidationConflictError):
        service.validate(OPAQUE_INVITATION_VALUE)

    assert identity.requested_user_id is None
    session.commit.assert_called_once_with()


@pytest.mark.parametrize(
    "target_user_id",
    [None, "@Employee:localhost", "@employee:other.example", "employee"],
)
def test_invalid_persisted_identity_fails_closed(
    target_user_id: str | None,
) -> None:
    service, session, _, _, _, identity = build_service(
        make_invitation(target_user_id=target_user_id)
    )

    with pytest.raises(ActivationValidationConflictError):
        service.validate(OPAQUE_INVITATION_VALUE)

    assert identity.requested_user_id is None
    session.commit.assert_called_once_with()


def test_unapproved_persisted_role_fails_closed() -> None:
    invitation = make_invitation()
    invitation.role = cast(InvitationRole, "platform_admin")
    service, session, _, _, _, identity = build_service(invitation)

    with pytest.raises(ActivationValidationConflictError):
        service.validate(OPAQUE_INVITATION_VALUE)

    assert identity.requested_user_id is None
    session.commit.assert_called_once_with()


def test_existing_synapse_account_is_generic_conflict() -> None:
    service, _, _, _, _, identity = build_service(make_invitation())
    identity.error = None

    with pytest.raises(ActivationValidationConflictError):
        service.validate(OPAQUE_INVITATION_VALUE)


def test_synapse_failure_propagates_after_local_transaction_is_closed() -> None:
    service, session, _, _, _, identity = build_service(make_invitation())
    identity.error = SynapseAdminUnavailableError()

    with pytest.raises(SynapseAdminUnavailableError):
        service.validate(OPAQUE_INVITATION_VALUE)

    session.commit.assert_called_once_with()


def test_local_limit_blocks_before_synapse_with_retry_after() -> None:
    service, session, _, _, limits, identity = build_service(make_invitation())
    limits.decision = ActivationRateLimitDecision(
        allowed=False,
        attempt_count=11,
        limit=10,
        retry_after_seconds=123,
        window_ends_at=NOW + timedelta(seconds=123),
    )

    with pytest.raises(ActivationValidationRateLimitedError) as captured:
        service.validate(OPAQUE_INVITATION_VALUE)

    assert captured.value.retry_after_seconds == 123
    assert identity.requested_user_id is None
    session.commit.assert_called_once_with()


def test_disappearing_invitation_is_not_counted_as_available() -> None:
    service, session, _, _, limits, identity = build_service(make_invitation())
    limits.decision = None

    with pytest.raises(ActivationValidationNotFoundError):
        service.validate(OPAQUE_INVITATION_VALUE)

    assert identity.requested_user_id is None
    session.rollback.assert_called_once_with()
    session.commit.assert_not_called()


def test_database_failure_rolls_back_and_fails_closed() -> None:
    service, session, _, _, limits, identity = build_service(make_invitation())
    limits.error = SQLAlchemyError("database detail")

    with pytest.raises(ActivationValidationStorageUnavailableError):
        service.validate(OPAQUE_INVITATION_VALUE)

    assert identity.requested_user_id is None
    session.rollback.assert_called_once_with()
    session.commit.assert_not_called()
