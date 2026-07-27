"""Interface local e códigos de saída da reconciliação."""

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from social_internal_backend.commands import reconcile_registration
from social_internal_backend.registrations import (
    ReconciliationDeviceStillPresentError,
    ReconciliationNotFoundError,
    ReconciliationStateError,
)
from social_internal_backend.synapse import SynapseAdminUnavailableError


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (ReconciliationNotFoundError(), 1),
        (ReconciliationStateError(), 2),
        (ReconciliationDeviceStillPresentError(), 3),
        (SynapseAdminUnavailableError(), 4),
        (SQLAlchemyError(), 5),
    ],
)
def test_command_maps_safe_local_errors(
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
    expected: int,
) -> None:
    engine = MagicMock()
    session = MagicMock()
    monkeypatch.setattr(reconcile_registration, "get_settings", MagicMock())
    monkeypatch.setattr(reconcile_registration, "build_engine", MagicMock(return_value=engine))
    monkeypatch.setattr(
        reconcile_registration,
        "build_session_factory",
        MagicMock(return_value=MagicMock(return_value=session)),
    )
    admin = MagicMock()
    admin.__enter__.return_value = admin
    monkeypatch.setattr(
        reconcile_registration,
        "SynapseAdminClient",
        MagicMock(return_value=admin),
    )
    service = MagicMock()
    service.reconcile.side_effect = error
    monkeypatch.setattr(
        reconcile_registration,
        "RegistrationReconciliationService",
        MagicMock(return_value=service),
    )

    assert reconcile_registration.main([str(uuid4())]) == expected
    engine.dispose.assert_called_once()


def test_command_reports_success(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = MagicMock()
    session = MagicMock()
    settings = SimpleNamespace(
        synapse_base_url="http://synapse",
        synapse_request_timeout_seconds=5,
        matrix_server_name="localhost",
        synapse_admin_access_token=MagicMock(),
    )
    monkeypatch.setattr(reconcile_registration, "get_settings", lambda: settings)
    monkeypatch.setattr(reconcile_registration, "build_engine", lambda value: engine)
    monkeypatch.setattr(
        reconcile_registration,
        "build_session_factory",
        lambda value: MagicMock(return_value=session),
    )
    admin = MagicMock()
    admin.__enter__.return_value = admin
    monkeypatch.setattr(
        reconcile_registration,
        "SynapseAdminClient",
        MagicMock(return_value=admin),
    )
    service = MagicMock()
    service.reconcile.return_value = SimpleNamespace(
        user_id="@employee:localhost",
        device_was_present=True,
    )
    monkeypatch.setattr(
        reconcile_registration,
        "RegistrationReconciliationService",
        MagicMock(return_value=service),
    )

    assert reconcile_registration.main([str(uuid4())]) == 0
    engine.dispose.assert_called_once()
