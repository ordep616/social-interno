"""Contrato transacional da unidade de trabalho do cadastro."""

import inspect
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from social_internal_backend.models import (
    Invitation,
    InvitationRole,
    InvitationStatus,
    RegistrationAttempt,
    RegistrationAttemptStatus,
    UserRole,
    UserRoleAssignment,
)
from social_internal_backend.registrations import (
    RegistrationCheckpointConflictError,
    RegistrationFinalizationConflictError,
    RegistrationReleaseConflictError,
    RegistrationReservationConflictError,
    RegistrationUnitOfWork,
)

NOW = datetime(2026, 7, 24, 15, tzinfo=UTC)
TOKEN_HASH = "a" * 64
TARGET_USER_ID = "@alice:localhost"
DEVICE_ID = "PROVISIONING"


def make_invitation(
    *,
    role: InvitationRole = InvitationRole.user,
    status: InvitationStatus = InvitationStatus.processing,
    target_user_id: str | None = TARGET_USER_ID,
) -> Invitation:
    return Invitation(
        id=uuid4(),
        token_hash=TOKEN_HASH,
        role=role,
        status=status,
        created_by="@admin:localhost",
        target_user_id=target_user_id,
        created_at=NOW - timedelta(hours=1),
        expires_at=NOW + timedelta(hours=23),
    )


def make_attempt(
    invitation: Invitation,
    *,
    status: RegistrationAttemptStatus = RegistrationAttemptStatus.synapse_created,
    matrix_user_id: str = TARGET_USER_ID,
    provisioning_device_id: str | None = DEVICE_ID,
    provisioning_session_revoked_at: datetime | None = NOW - timedelta(minutes=1),
) -> RegistrationAttempt:
    return RegistrationAttempt(
        id=uuid4(),
        invitation_id=invitation.id,
        matrix_user_id=matrix_user_id,
        role=invitation.role,
        status=status,
        created_at=NOW - timedelta(minutes=2),
        updated_at=NOW - timedelta(minutes=1),
        provisioning_device_id=provisioning_device_id,
        provisioning_session_revoked_at=provisioning_session_revoked_at,
    )


def make_unit_of_work(
    *,
    session: MagicMock,
    invitations: MagicMock,
    attempts: MagicMock,
    roles: MagicMock,
) -> RegistrationUnitOfWork:
    return RegistrationUnitOfWork(
        session,
        invitation_repository=invitations,
        attempt_repository=attempts,
        role_repository=roles,
    )


def test_public_operations_never_accept_password_token_or_access_token() -> None:
    for method_name in {
        "reserve",
        "record_synapse_created",
        "record_reconciliation_required",
        "record_provisioning_session_revoked",
        "release",
        "finalize",
    }:
        parameter_names = set(
            inspect.signature(getattr(RegistrationUnitOfWork, method_name)).parameters
        )
        assert "password" not in parameter_names
        assert "token" not in parameter_names
        assert "access_token" not in parameter_names


def test_reservation_derives_identity_and_role_from_invitation() -> None:
    session = MagicMock(spec=Session)
    invitations = MagicMock()
    attempts = MagicMock()
    roles = MagicMock()
    invitation = make_invitation(role=InvitationRole.group_admin)
    invitations.claim_pending.return_value = invitation
    unit_of_work = make_unit_of_work(
        session=session,
        invitations=invitations,
        attempts=attempts,
        roles=roles,
    )

    result = unit_of_work.reserve(token_hash=TOKEN_HASH, now=NOW)

    invitations.claim_pending.assert_called_once_with(TOKEN_HASH, NOW)
    attempts.add.assert_called_once()
    persisted_attempt = attempts.add.call_args.args[0]
    assert result.invitation is invitation
    assert result.attempt is persisted_attempt
    assert persisted_attempt.invitation_id == invitation.id
    assert persisted_attempt.matrix_user_id == TARGET_USER_ID
    assert persisted_attempt.role is InvitationRole.group_admin
    assert persisted_attempt.status is RegistrationAttemptStatus.processing
    assert persisted_attempt.provisioning_device_id is None
    assert persisted_attempt.provisioning_session_revoked_at is None
    session.commit.assert_called_once_with()
    session.rollback.assert_not_called()
    roles.assert_not_called()


@pytest.mark.parametrize(
    "invitation",
    [
        None,
        make_invitation(status=InvitationStatus.pending),
        make_invitation(target_user_id=None),
    ],
)
def test_reservation_rejects_missing_or_inconsistent_authority(
    invitation: Invitation | None,
) -> None:
    session = MagicMock(spec=Session)
    invitations = MagicMock()
    attempts = MagicMock()
    roles = MagicMock()
    invitations.claim_pending.return_value = invitation
    unit_of_work = make_unit_of_work(
        session=session,
        invitations=invitations,
        attempts=attempts,
        roles=roles,
    )

    with pytest.raises(RegistrationReservationConflictError):
        unit_of_work.reserve(token_hash=TOKEN_HASH, now=NOW)

    attempts.add.assert_not_called()
    session.commit.assert_not_called()
    session.rollback.assert_called_once_with()


def test_reservation_sanitizes_integrity_error_and_rolls_back() -> None:
    session = MagicMock(spec=Session)
    invitations = MagicMock()
    attempts = MagicMock()
    roles = MagicMock()
    invitations.claim_pending.return_value = make_invitation()
    attempts.add.side_effect = IntegrityError("statement", {}, Exception("database detail"))
    unit_of_work = make_unit_of_work(
        session=session,
        invitations=invitations,
        attempts=attempts,
        roles=roles,
    )

    with pytest.raises(RegistrationReservationConflictError) as captured:
        unit_of_work.reserve(token_hash=TOKEN_HASH, now=NOW)

    assert captured.value.args == ()
    assert captured.value.__cause__ is None
    session.commit.assert_not_called()
    session.rollback.assert_called_once_with()


def test_checkpoint_methods_commit_only_successful_conditional_transitions() -> None:
    session = MagicMock(spec=Session)
    invitations = MagicMock()
    attempts = MagicMock()
    roles = MagicMock()
    invitation = make_invitation()
    attempt = make_attempt(invitation)
    attempts.mark_synapse_created.return_value = attempt
    attempts.mark_reconciliation_required.return_value = attempt
    attempts.mark_provisioning_session_revoked.return_value = attempt
    unit_of_work = make_unit_of_work(
        session=session,
        invitations=invitations,
        attempts=attempts,
        roles=roles,
    )

    assert (
        unit_of_work.record_synapse_created(
            attempt_id=attempt.id,
            provisioning_device_id=DEVICE_ID,
            now=NOW,
        )
        is attempt
    )
    assert (
        unit_of_work.record_reconciliation_required(
            attempt_id=attempt.id,
            failure_code="revocation_result_ambiguous",
            now=NOW,
        )
        is attempt
    )
    assert (
        unit_of_work.record_provisioning_session_revoked(
            attempt_id=attempt.id,
            provisioning_device_id=DEVICE_ID,
            now=NOW,
        )
        is attempt
    )

    attempts.mark_synapse_created.assert_called_once_with(
        attempt.id,
        provisioning_device_id=DEVICE_ID,
        now=NOW,
    )
    attempts.mark_reconciliation_required.assert_called_once_with(
        attempt.id,
        failure_code="revocation_result_ambiguous",
        now=NOW,
    )
    attempts.mark_provisioning_session_revoked.assert_called_once_with(
        attempt.id,
        provisioning_device_id=DEVICE_ID,
        now=NOW,
    )
    assert session.commit.call_count == 3
    session.rollback.assert_not_called()


def test_checkpoint_conflict_is_sanitized_and_rolled_back() -> None:
    session = MagicMock(spec=Session)
    invitations = MagicMock()
    attempts = MagicMock()
    roles = MagicMock()
    attempts.mark_synapse_created.return_value = None
    unit_of_work = make_unit_of_work(
        session=session,
        invitations=invitations,
        attempts=attempts,
        roles=roles,
    )

    with pytest.raises(RegistrationCheckpointConflictError) as captured:
        unit_of_work.record_synapse_created(
            attempt_id=uuid4(),
            provisioning_device_id=DEVICE_ID,
            now=NOW,
        )

    assert captured.value.args == ()
    session.commit.assert_not_called()
    session.rollback.assert_called_once_with()


def test_release_updates_attempt_and_matching_invitation_before_commit() -> None:
    session = MagicMock(spec=Session)
    invitations = MagicMock()
    attempts = MagicMock()
    roles = MagicMock()
    invitation = make_invitation()
    attempt = make_attempt(
        invitation,
        status=RegistrationAttemptStatus.processing,
        provisioning_device_id=None,
        provisioning_session_revoked_at=None,
    )
    released_invitation = make_invitation(status=InvitationStatus.pending)
    released_invitation.id = invitation.id
    released_attempt = make_attempt(
        invitation,
        status=RegistrationAttemptStatus.released,
        provisioning_device_id=None,
        provisioning_session_revoked_at=None,
    )
    released_attempt.id = attempt.id
    released_attempt.failure_code = "creation_not_started"
    attempts.get.return_value = attempt
    invitations.get.return_value = invitation
    attempts.mark_released.return_value = released_attempt
    invitations.release_processing.return_value = released_invitation
    unit_of_work = make_unit_of_work(
        session=session,
        invitations=invitations,
        attempts=attempts,
        roles=roles,
    )

    result = unit_of_work.release(
        attempt_id=attempt.id,
        failure_code="creation_not_started",
        now=NOW,
    )

    attempts.mark_released.assert_called_once_with(
        attempt.id,
        failure_code="creation_not_started",
        now=NOW,
    )
    invitations.release_processing.assert_called_once_with(invitation.id, NOW)
    assert result.attempt is released_attempt
    assert result.invitation is released_invitation
    session.commit.assert_called_once_with()
    session.rollback.assert_not_called()


def test_release_rejects_identity_divergence_without_mutation() -> None:
    session = MagicMock(spec=Session)
    invitations = MagicMock()
    attempts = MagicMock()
    roles = MagicMock()
    invitation = make_invitation()
    attempt = make_attempt(
        invitation,
        status=RegistrationAttemptStatus.processing,
        matrix_user_id="@other:localhost",
        provisioning_device_id=None,
        provisioning_session_revoked_at=None,
    )
    attempts.get.return_value = attempt
    invitations.get.return_value = invitation
    unit_of_work = make_unit_of_work(
        session=session,
        invitations=invitations,
        attempts=attempts,
        roles=roles,
    )

    with pytest.raises(RegistrationReleaseConflictError):
        unit_of_work.release(
            attempt_id=attempt.id,
            failure_code="creation_not_started",
            now=NOW,
        )

    attempts.mark_released.assert_not_called()
    invitations.release_processing.assert_not_called()
    session.commit.assert_not_called()
    session.rollback.assert_called_once_with()


@pytest.mark.parametrize(
    ("invitation_role", "expected_role"),
    [
        (InvitationRole.user, UserRole.user),
        (InvitationRole.group_admin, UserRole.group_admin),
    ],
)
def test_finalization_requires_evidence_and_commits_all_local_records(
    invitation_role: InvitationRole,
    expected_role: UserRole,
) -> None:
    session = MagicMock(spec=Session)
    invitations = MagicMock()
    attempts = MagicMock()
    roles = MagicMock()
    invitation = make_invitation(role=invitation_role)
    attempt = make_attempt(invitation)
    completed_invitation = make_invitation(
        role=invitation_role,
        status=InvitationStatus.used,
    )
    completed_invitation.id = invitation.id
    completed_attempt = make_attempt(
        invitation,
        status=RegistrationAttemptStatus.completed,
    )
    completed_attempt.id = attempt.id
    completed_attempt.completed_at = NOW
    attempts.get.return_value = attempt
    invitations.get.return_value = invitation
    invitations.complete_processing.return_value = completed_invitation
    attempts.mark_completed.return_value = completed_attempt
    unit_of_work = make_unit_of_work(
        session=session,
        invitations=invitations,
        attempts=attempts,
        roles=roles,
    )

    result = unit_of_work.finalize(attempt_id=attempt.id, now=NOW)

    invitations.complete_processing.assert_called_once_with(
        invitation.id,
        TARGET_USER_ID,
        NOW,
    )
    attempts.mark_completed.assert_called_once_with(attempt.id, NOW)
    roles.add.assert_called_once()
    assignment = roles.add.call_args.args[0]
    assert isinstance(assignment, UserRoleAssignment)
    assert assignment.matrix_user_id == TARGET_USER_ID
    assert assignment.role is expected_role
    assert assignment.granted_by == invitation.created_by
    assert result.invitation is completed_invitation
    assert result.attempt is completed_attempt
    assert result.role_assignment is assignment
    session.commit.assert_called_once_with()
    session.rollback.assert_not_called()


@pytest.mark.parametrize(
    (
        "status",
        "provisioning_device_id",
        "provisioning_session_revoked_at",
    ),
    [
        (RegistrationAttemptStatus.processing, None, None),
        (RegistrationAttemptStatus.synapse_created, None, NOW - timedelta(minutes=1)),
        (RegistrationAttemptStatus.synapse_created, DEVICE_ID, None),
        (RegistrationAttemptStatus.reconciliation_required, DEVICE_ID, None),
        (RegistrationAttemptStatus.completed, DEVICE_ID, NOW - timedelta(minutes=1)),
    ],
)
def test_finalization_rejects_attempt_without_exact_revocation_preconditions(
    status: RegistrationAttemptStatus,
    provisioning_device_id: str | None,
    provisioning_session_revoked_at: datetime | None,
) -> None:
    session = MagicMock(spec=Session)
    invitations = MagicMock()
    attempts = MagicMock()
    roles = MagicMock()
    invitation = make_invitation()
    attempt = make_attempt(
        invitation,
        status=status,
        provisioning_device_id=provisioning_device_id,
        provisioning_session_revoked_at=provisioning_session_revoked_at,
    )
    attempts.get.return_value = attempt
    unit_of_work = make_unit_of_work(
        session=session,
        invitations=invitations,
        attempts=attempts,
        roles=roles,
    )

    with pytest.raises(RegistrationFinalizationConflictError):
        unit_of_work.finalize(attempt_id=attempt.id, now=NOW)

    invitations.get.assert_not_called()
    invitations.complete_processing.assert_not_called()
    attempts.mark_completed.assert_not_called()
    roles.add.assert_not_called()
    session.commit.assert_not_called()
    session.rollback.assert_called_once_with()


def test_finalization_integrity_error_rolls_back_all_local_changes() -> None:
    session = MagicMock(spec=Session)
    invitations = MagicMock()
    attempts = MagicMock()
    roles = MagicMock()
    invitation = make_invitation()
    attempt = make_attempt(invitation)
    attempts.get.return_value = attempt
    invitations.get.return_value = invitation
    invitations.complete_processing.return_value = invitation
    attempts.mark_completed.return_value = attempt
    roles.add.side_effect = IntegrityError("statement", {}, Exception("database detail"))
    unit_of_work = make_unit_of_work(
        session=session,
        invitations=invitations,
        attempts=attempts,
        roles=roles,
    )

    with pytest.raises(RegistrationFinalizationConflictError) as captured:
        unit_of_work.finalize(attempt_id=attempt.id, now=NOW)

    assert captured.value.args == ()
    assert captured.value.__cause__ is None
    invitations.complete_processing.assert_called_once()
    attempts.mark_completed.assert_called_once()
    roles.add.assert_called_once()
    session.commit.assert_not_called()
    session.rollback.assert_called_once_with()
