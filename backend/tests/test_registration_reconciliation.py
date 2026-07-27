"""Reconciliação que nunca repete a criação da conta."""

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from social_internal_backend.models import RegistrationAttemptStatus
from social_internal_backend.registrations import (
    ReconciliationDeviceStillPresentError,
    ReconciliationNotFoundError,
    ReconciliationStateError,
    RegistrationReconciliationService,
)
from social_internal_backend.synapse import SynapseUserNotFoundError

NOW = datetime(2026, 7, 27, 18, tzinfo=UTC)
ATTEMPT_ID = uuid4()


def build_service(*, device_present: bool) -> tuple[RegistrationReconciliationService, MagicMock]:
    admin = MagicMock()
    if device_present:
        admin.get_device.side_effect = [None, SynapseUserNotFoundError()]
    else:
        admin.get_device.side_effect = SynapseUserNotFoundError()
    service = RegistrationReconciliationService(
        MagicMock(),
        admin_provider=admin,
        clock=lambda: NOW,
    )
    attempt = SimpleNamespace(
        id=ATTEMPT_ID,
        status=RegistrationAttemptStatus.reconciliation_required,
        matrix_user_id="@employee:localhost",
        provisioning_device_id="PROVISIONING",
    )
    service._attempts = MagicMock()
    service._attempts.get.return_value = attempt
    service._uow = MagicMock()
    return service, admin


@pytest.mark.parametrize("device_present", [True, False])
def test_reconciliation_confirms_absence_then_finalizes(device_present: bool) -> None:
    service, admin = build_service(device_present=device_present)

    result = service.reconcile(ATTEMPT_ID)
    uow = cast(MagicMock, service._uow)

    assert result.user_id == "@employee:localhost"
    assert result.device_was_present is device_present
    assert admin.delete_device.call_count == int(device_present)
    uow.record_provisioning_session_revoked.assert_called_once_with(
        attempt_id=ATTEMPT_ID,
        provisioning_device_id="PROVISIONING",
        now=NOW,
    )
    uow.finalize.assert_called_once_with(attempt_id=ATTEMPT_ID, now=NOW)


def test_unknown_or_incomplete_attempt_stays_blocked() -> None:
    service, _ = build_service(device_present=False)
    attempts = cast(MagicMock, service._attempts)
    attempts.get.return_value = None
    with pytest.raises(ReconciliationNotFoundError):
        service.reconcile(ATTEMPT_ID)

    attempts.get.return_value = SimpleNamespace(
        status=RegistrationAttemptStatus.reconciliation_required,
        provisioning_device_id=None,
    )
    with pytest.raises(ReconciliationStateError):
        service.reconcile(ATTEMPT_ID)


def test_device_still_present_prevents_local_completion() -> None:
    service, admin = build_service(device_present=True)
    uow = cast(MagicMock, service._uow)
    admin.get_device.side_effect = None
    with pytest.raises(ReconciliationDeviceStillPresentError):
        service.reconcile(ATTEMPT_ID)
    uow.record_provisioning_session_revoked.assert_not_called()
    uow.finalize.assert_not_called()
