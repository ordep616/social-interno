"""Serviço de contas apoiado pelas APIs administrativas suportadas do Synapse."""

from dataclasses import dataclass
from typing import Protocol

from pydantic import SecretStr

from social_internal_backend.synapse import SynapseUser, SynapseUserPage


class SynapseAccountAdminPort(Protocol):
    """Contrato mínimo do cliente Synapse usado pelo serviço."""

    def list_users(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        query: str | None = None,
    ) -> SynapseUserPage: ...

    def update_user(
        self,
        *,
        user_id: str,
        display_name: str | None = None,
        locked: bool | None = None,
    ) -> SynapseUser: ...

    def reset_password(
        self,
        *,
        user_id: str,
        new_password: SecretStr,
        logout_devices: bool = True,
    ) -> None: ...

    def deactivate_user(self, *, user_id: str, erase: bool) -> None: ...


@dataclass(frozen=True, slots=True)
class AccountService:
    """Mantém o token administrativo restrito ao backend."""

    synapse_admin: SynapseAccountAdminPort

    def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        query: str | None = None,
    ) -> SynapseUserPage:
        """Lista contas locais."""

        return self.synapse_admin.list_users(offset=offset, limit=limit, query=query)

    def update(
        self,
        *,
        user_id: str,
        display_name: str | None = None,
        locked: bool | None = None,
    ) -> SynapseUser:
        """Atualiza dados editáveis de uma conta local."""

        return self.synapse_admin.update_user(
            user_id=user_id,
            display_name=display_name,
            locked=locked,
        )

    def reset_password(
        self,
        *,
        user_id: str,
        new_password: SecretStr,
        logout_devices: bool = True,
    ) -> None:
        """Redefine senha sem persistir o segredo."""

        self.synapse_admin.reset_password(
            user_id=user_id,
            new_password=new_password,
            logout_devices=logout_devices,
        )

    def deactivate(self, *, user_id: str, erase: bool) -> None:
        """Desativa uma conta local."""

        self.synapse_admin.deactivate_user(user_id=user_id, erase=erase)
