"""Orquestração do cadastro sem persistência de token ou senha."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from pydantic import SecretStr

from social_internal_backend.invitations.tokens import hash_invitation_token
from social_internal_backend.models import InvitationStatus
from social_internal_backend.rate_limits import ActivationRateLimitDecision
from social_internal_backend.registrations import (
    RegistrationConflictError,
    RegistrationNotFoundError,
    RegistrationPasswordPolicyError,
    RegistrationRateLimitedError,
    RegistrationService,
    RegistrationUnavailableError,
)
from social_internal_backend.synapse import (
    InvalidMatrixAccessTokenError,
    MatrixIdentity,
    ProvisioningSession,
    SynapseRegistrationConflictError,
    SynapseRegistrationProtocolError,
    SynapseRegistrationUnavailableError,
    SynapseUserNotFoundError,
)

NOW = datetime(2026, 7, 27, 12, tzinfo=UTC)
OPAQUE_INVITATION_VALUE = "opaque-registration-invitation"
OPAQUE_PASSWORD_VALUE = "opaque-password-value"  # noqa: S105
ATTEMPT_ID = uuid4()


class RegistrationProvider:
    def register(self, *, username: str, password: SecretStr) -> ProvisioningSession:
        assert username == "employee"
        assert password.get_secret_value() == OPAQUE_PASSWORD_VALUE
        return ProvisioningSession(
            user_id="@employee:localhost",
            device_id="PROVISIONING",
            access_token=SecretStr("ephemeral-access-value"),
        )


class IdentityProvider:
    calls = 0

    def whoami(self, access_token: str) -> MatrixIdentity:
        assert access_token == "ephemeral-access-value"  # noqa: S105
        self.calls += 1
        if self.calls == 1:
            return MatrixIdentity(
                user_id="@employee:localhost",
                is_guest=False,
                device_id="PROVISIONING",
            )
        raise InvalidMatrixAccessTokenError


class AdminProvider:
    device_deleted = False

    def get_user(self, user_id: str) -> object:
        assert user_id == "@employee:localhost"
        raise SynapseUserNotFoundError

    def get_device(self, *, user_id: str, device_id: str) -> None:
        assert (user_id, device_id) == ("@employee:localhost", "PROVISIONING")
        if self.device_deleted:
            raise SynapseUserNotFoundError

    def delete_device(self, *, user_id: str, device_id: str) -> None:
        assert (user_id, device_id) == ("@employee:localhost", "PROVISIONING")
        self.device_deleted = True


def build_service(
    *,
    invitation_status: InvitationStatus = InvitationStatus.pending,
    allowed: bool = True,
) -> tuple[RegistrationService, MagicMock]:
    session = MagicMock()
    service = RegistrationService(
        session,
        registration_provider=RegistrationProvider(),
        identity_provider=IdentityProvider(),
        admin_provider=AdminProvider(),
        matrix_server_name="localhost",
        clock=lambda: NOW,
    )
    invitation = SimpleNamespace(
        status=invitation_status,
        expires_at=NOW + timedelta(hours=1),
    )
    invitations = MagicMock()
    invitations.get_by_token_hash.return_value = invitation
    limits = MagicMock()
    limits.consume_existing_invitation.return_value = ActivationRateLimitDecision(
        allowed=allowed,
        attempt_count=1,
        limit=5,
        retry_after_seconds=60,
        window_ends_at=NOW + timedelta(minutes=15),
    )
    attempt = SimpleNamespace(id=ATTEMPT_ID, matrix_user_id="@employee:localhost")
    uow = MagicMock()
    uow.reserve.return_value = SimpleNamespace(attempt=attempt)
    uow.finalize.return_value = SimpleNamespace(attempt=attempt)
    service._invitations = invitations
    service._limits = limits
    service._uow = uow
    return service, uow


def test_success_follows_durable_revocation_order() -> None:
    service, uow = build_service()

    result = service.register(
        OPAQUE_INVITATION_VALUE,
        SecretStr(OPAQUE_PASSWORD_VALUE),
    )

    assert result.user_id == "@employee:localhost"
    uow.reserve.assert_called_once_with(
        token_hash=hash_invitation_token(OPAQUE_INVITATION_VALUE),
        now=NOW,
    )
    uow.record_synapse_created.assert_called_once_with(
        attempt_id=ATTEMPT_ID,
        provisioning_device_id="PROVISIONING",
        now=NOW,
    )
    uow.record_provisioning_session_revoked.assert_called_once_with(
        attempt_id=ATTEMPT_ID,
        provisioning_device_id="PROVISIONING",
        now=NOW,
    )
    uow.finalize.assert_called_once_with(attempt_id=ATTEMPT_ID, now=NOW)


def test_password_is_rejected_before_persistence() -> None:
    service, uow = build_service()
    with pytest.raises(RegistrationPasswordPolicyError):
        service.register(OPAQUE_INVITATION_VALUE, SecretStr("short"))
    uow.reserve.assert_not_called()


def test_rate_limit_blocks_before_reservation() -> None:
    service, uow = build_service(allowed=False)
    with pytest.raises(RegistrationRateLimitedError) as captured:
        service.register(
            OPAQUE_INVITATION_VALUE,
            SecretStr(OPAQUE_PASSWORD_VALUE),
        )
    assert captured.value.retry_after_seconds == 60
    uow.reserve.assert_not_called()


@pytest.mark.parametrize(
    "status",
    [
        InvitationStatus.used,
        InvitationStatus.revoked,
        InvitationStatus.expired,
    ],
)
def test_terminal_invitation_is_unavailable(status: InvitationStatus) -> None:
    service, uow = build_service(invitation_status=status)
    with pytest.raises(RegistrationUnavailableError):
        service.register(
            OPAQUE_INVITATION_VALUE,
            SecretStr(OPAQUE_PASSWORD_VALUE),
        )
    uow.reserve.assert_not_called()


def test_processing_invitation_is_a_conflict() -> None:
    service, uow = build_service(invitation_status=InvitationStatus.processing)
    with pytest.raises(RegistrationConflictError):
        service.register(
            OPAQUE_INVITATION_VALUE,
            SecretStr(OPAQUE_PASSWORD_VALUE),
        )
    uow.reserve.assert_not_called()


class FailingRegistrationProvider:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def register(self, *, username: str, password: SecretStr) -> ProvisioningSession:
        del username, password
        raise self.error


@pytest.mark.parametrize(
    ("error", "expected_error", "uow_method"),
    [
        (
            SynapseRegistrationConflictError(),
            RegistrationConflictError,
            "conflict_identity",
        ),
        (
            SynapseRegistrationUnavailableError(ambiguous=False),
            Exception,
            "release",
        ),
        (
            SynapseRegistrationUnavailableError(ambiguous=True),
            Exception,
            "record_reconciliation_required",
        ),
        (
            SynapseRegistrationProtocolError(ambiguous=True),
            Exception,
            "record_reconciliation_required",
        ),
    ],
)
def test_creation_failures_are_checkpointed(
    error: Exception,
    expected_error: type[Exception],
    uow_method: str,
) -> None:
    service, uow = build_service()
    service._registration_provider = FailingRegistrationProvider(error)
    with pytest.raises(expected_error):
        service.register(
            OPAQUE_INVITATION_VALUE,
            SecretStr(OPAQUE_PASSWORD_VALUE),
        )
    getattr(uow, uow_method).assert_called_once()


def test_account_race_becomes_terminal_conflict() -> None:
    service, uow = build_service()
    admin = MagicMock()
    admin.get_user.return_value = object()
    service._admin_provider = admin
    with pytest.raises(RegistrationConflictError):
        service.register(
            OPAQUE_INVITATION_VALUE,
            SecretStr(OPAQUE_PASSWORD_VALUE),
        )
    uow.conflict_identity.assert_called_once()


def test_unknown_invitation_is_not_rate_limited_or_reserved() -> None:
    service, uow = build_service()
    invitations = cast(MagicMock, service._invitations)
    limits = cast(MagicMock, service._limits)
    invitations.get_by_token_hash.return_value = None
    with pytest.raises(RegistrationNotFoundError):
        service.register(
            OPAQUE_INVITATION_VALUE,
            SecretStr(OPAQUE_PASSWORD_VALUE),
        )
    limits.consume_existing_invitation.assert_not_called()
    uow.reserve.assert_not_called()


def test_missing_counter_decision_fails_as_not_found() -> None:
    service, uow = build_service()
    limits = cast(MagicMock, service._limits)
    limits.consume_existing_invitation.return_value = None
    with pytest.raises(RegistrationNotFoundError):
        service.register(
            OPAQUE_INVITATION_VALUE,
            SecretStr(OPAQUE_PASSWORD_VALUE),
        )
    uow.reserve.assert_not_called()
