"""Autorização interna das operações administrativas."""

from dataclasses import dataclass
from typing import Protocol

from social_internal_backend.models import UserRole, UserRoleAssignment
from social_internal_backend.synapse import MatrixIdentity


class IdentityProvider(Protocol):
    """Contrato mínimo para validar uma credencial Matrix."""

    def whoami(self, access_token: str) -> MatrixIdentity: ...


class UserRoleRepositoryPort(Protocol):
    """Consulta mínima ao banco próprio de papéis."""

    def get(self, matrix_user_id: str) -> UserRoleAssignment | None: ...


class PlatformAdminAccessDeniedError(Exception):
    """A identidade é válida, mas não possui administração da plataforma."""


class CorporateUserAccessDeniedError(Exception):
    """A identidade não pertence a uma conta corporativa autorizada."""


@dataclass(frozen=True, slots=True)
class UserCapabilitiesContext:
    """Papel e capacidades calculados sem conservar a credencial Matrix."""

    identity: MatrixIdentity
    assignment: UserRoleAssignment

    @property
    def can_manage_user_activations(self) -> bool:
        """Permite gerenciamento somente ao papel administrativo da plataforma."""

        return self.assignment.role is UserRole.platform_admin


@dataclass(frozen=True, slots=True)
class AuthorizedPlatformAdmin:
    """Contexto autorizado sem conservar a credencial Matrix."""

    identity: MatrixIdentity
    assignment: UserRoleAssignment


class UserCapabilitiesService:
    """Resolve o papel corporativo da identidade confirmada pelo Synapse."""

    def __init__(
        self,
        *,
        identity_provider: IdentityProvider,
        role_repository: UserRoleRepositoryPort,
    ) -> None:
        self._identity_provider = identity_provider
        self._role_repository = role_repository

    def resolve(self, access_token: str) -> UserCapabilitiesContext:
        """Retorna capacidades para usuário não convidado com papel local."""

        identity = self._identity_provider.whoami(access_token)
        if identity.is_guest:
            raise CorporateUserAccessDeniedError

        assignment = self._role_repository.get(identity.user_id)
        if assignment is None:
            raise CorporateUserAccessDeniedError

        return UserCapabilitiesContext(identity=identity, assignment=assignment)


class PlatformAdminAuthorizationService:
    """Combina a identidade confirmada pelo Synapse com o papel local."""

    def __init__(
        self,
        *,
        identity_provider: IdentityProvider,
        role_repository: UserRoleRepositoryPort,
    ) -> None:
        self._identity_provider = identity_provider
        self._role_repository = role_repository

    def authorize(self, access_token: str) -> AuthorizedPlatformAdmin:
        """Autoriza exclusivamente usuário não convidado com `platform_admin`."""

        identity = self._identity_provider.whoami(access_token)
        if identity.is_guest:
            raise PlatformAdminAccessDeniedError

        assignment = self._role_repository.get(identity.user_id)
        if assignment is None or assignment.role is not UserRole.platform_admin:
            raise PlatformAdminAccessDeniedError

        return AuthorizedPlatformAdmin(identity=identity, assignment=assignment)
