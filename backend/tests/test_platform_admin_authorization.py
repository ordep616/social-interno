"""Combinação da identidade Matrix com o papel corporativo."""

from datetime import UTC, datetime

import pytest

from social_internal_backend.authorization import (
    PlatformAdminAccessDeniedError,
    PlatformAdminAuthorizationService,
)
from social_internal_backend.models import UserRole, UserRoleAssignment
from social_internal_backend.synapse import MatrixIdentity, SynapseUnavailableError

OPAQUE_VALUE = "opaque-value-for-tests"


def make_assignment(role: UserRole) -> UserRoleAssignment:
    return UserRoleAssignment(
        matrix_user_id="@admin:localhost",
        role=role,
        granted_at=datetime(2026, 7, 23, 10, tzinfo=UTC),
        granted_by=None,
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
) -> tuple[PlatformAdminAuthorizationService, FakeIdentityProvider, FakeRoleRepository]:
    provider = FakeIdentityProvider(
        identity
        or MatrixIdentity(
            user_id="@admin:localhost",
            is_guest=False,
            device_id="DEVICE",
        )
    )
    repository = FakeRoleRepository(assignment)
    return (
        PlatformAdminAuthorizationService(
            identity_provider=provider,
            role_repository=repository,
        ),
        provider,
        repository,
    )


def test_authorizes_only_platform_admin_without_retaining_token() -> None:
    assignment = make_assignment(UserRole.platform_admin)
    service, _, repository = make_service(assignment=assignment)

    authorized = service.authorize(OPAQUE_VALUE)

    assert authorized.identity.user_id == "@admin:localhost"
    assert authorized.assignment is assignment
    assert repository.requested_user_id == "@admin:localhost"
    assert OPAQUE_VALUE not in repr(authorized)


def test_guest_is_denied_before_local_role_lookup() -> None:
    identity = MatrixIdentity(user_id="@admin:localhost", is_guest=True, device_id=None)
    service, _, repository = make_service(
        identity=identity,
        assignment=make_assignment(UserRole.platform_admin),
    )

    with pytest.raises(PlatformAdminAccessDeniedError):
        service.authorize(OPAQUE_VALUE)
    assert repository.requested_user_id is None


@pytest.mark.parametrize("role", [None, UserRole.user, UserRole.group_admin])
def test_missing_or_non_platform_role_is_denied(role: UserRole | None) -> None:
    assignment = make_assignment(role) if role is not None else None
    service, _, _ = make_service(assignment=assignment)

    with pytest.raises(PlatformAdminAccessDeniedError):
        service.authorize(OPAQUE_VALUE)


def test_identity_provider_failure_is_preserved_without_role_lookup() -> None:
    service, provider, repository = make_service(
        assignment=make_assignment(UserRole.platform_admin)
    )
    provider.error = SynapseUnavailableError()

    with pytest.raises(SynapseUnavailableError):
        service.authorize(OPAQUE_VALUE)
    assert repository.requested_user_id is None
