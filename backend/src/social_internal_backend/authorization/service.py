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


@dataclass(frozen=True, slots=True)
class AuthorizedPlatformAdmin:
    """Contexto autorizado sem conservar a credencial Matrix."""

    identity: MatrixIdentity
    assignment: UserRoleAssignment


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
