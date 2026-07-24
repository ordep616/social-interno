"""Resolução segura das capacidades corporativas."""

from datetime import UTC, datetime

import pytest

from social_internal_backend.authorization import (
    CorporateUserAccessDeniedError,
    UserCapabilitiesService,
)
from social_internal_backend.models import UserRole, UserRoleAssignment
from social_internal_backend.synapse import MatrixIdentity, SynapseUnavailableError

OPAQUE_VALUE = "opaque-value-for-tests"
USER_ID = "@employee:localhost"


def make_assignment(role: UserRole) -> UserRoleAssignment:
    return UserRoleAssignment(
        matrix_user_id=USER_ID,
        role=role,
        granted_at=datetime(2026, 7, 23, 10, tzinfo=UTC),
        granted_by="@admin:localhost",
    )


class FakeIdentityProvider:
    def __init__(self, identity: MatrixIdentity) -> None:
        self.identity = identity
        self.error: Exception | None = None

    def whoami(self, access_token: str) -> MatrixIdentity:
        assert access_token == OPAQUE_VALUE
        if self.error is not None:
            raise self.error
        return self.identity


class FakeRoleRepository:
    def __init__(self, assignment: UserRoleAssignment | None) -> None:
        self.assignment = assignment
        self.requested_user_id: str | None = None

    def get(self, matrix_user_id: str) -> UserRoleAssignment | None:
        self.requested_user_id = matrix_user_id
        return self.assignment


def make_service(
    *,
    identity: MatrixIdentity | None = None,
    assignment: UserRoleAssignment | None = None,
) -> tuple[UserCapabilitiesService, FakeIdentityProvider, FakeRoleRepository]:
    provider = FakeIdentityProvider(
        identity
        or MatrixIdentity(
            user_id=USER_ID,
            is_guest=False,
            device_id="DEVICE",
        )
    )
    repository = FakeRoleRepository(assignment)
    return (
        UserCapabilitiesService(
            identity_provider=provider,
            role_repository=repository,
        ),
        provider,
        repository,
    )


@pytest.mark.parametrize(
    ("role", "expected_capability"),
    [
        (UserRole.user, False),
        (UserRole.group_admin, False),
        (UserRole.platform_admin, True),
    ],
)
def test_resolves_capability_exclusively_from_local_role(
    role: UserRole,
    expected_capability: bool,
) -> None:
    assignment = make_assignment(role)
    service, _, repository = make_service(assignment=assignment)

    resolved = service.resolve(OPAQUE_VALUE)

    assert resolved.identity.user_id == USER_ID
    assert resolved.assignment is assignment
    assert resolved.can_manage_user_activations is expected_capability
    assert repository.requested_user_id == USER_ID
    assert OPAQUE_VALUE not in repr(resolved)


def test_guest_is_denied_before_local_role_lookup() -> None:
    identity = MatrixIdentity(user_id=USER_ID, is_guest=True, device_id=None)
    service, _, repository = make_service(
        identity=identity,
        assignment=make_assignment(UserRole.platform_admin),
    )

    with pytest.raises(CorporateUserAccessDeniedError):
        service.resolve(OPAQUE_VALUE)

    assert repository.requested_user_id is None


def test_identity_without_local_role_is_denied() -> None:
    service, _, repository = make_service(assignment=None)

    with pytest.raises(CorporateUserAccessDeniedError):
        service.resolve(OPAQUE_VALUE)

    assert repository.requested_user_id == USER_ID


def test_identity_provider_failure_is_preserved_without_role_lookup() -> None:
    service, provider, repository = make_service(
        assignment=make_assignment(UserRole.platform_admin)
    )
    provider.error = SynapseUnavailableError()

    with pytest.raises(SynapseUnavailableError):
        service.resolve(OPAQUE_VALUE)

    assert repository.requested_user_id is None
