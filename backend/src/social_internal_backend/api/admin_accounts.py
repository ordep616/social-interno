"""Endpoints REST administrativos de contas."""

from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator

from social_internal_backend.api.dependencies import (
    NO_STORE_HEADERS,
    AccountServiceDependency,
    AuditServiceDependency,
    PlatformAdmin,
)
from social_internal_backend.models import AuditAction, AuditResult, UserRole
from social_internal_backend.synapse import (
    InvalidSynapseAdminCredentialError,
    SynapseAdminProtocolError,
    SynapseAdminRateLimitedError,
    SynapseAdminUnavailableError,
    SynapseUser,
    SynapseUserAlreadyExistsError,
    SynapseUserNotFoundError,
)

router = APIRouter(prefix="/v1/admin/accounts", tags=["admin accounts"])


class AccountAdminResponse(BaseModel):
    """Representação administrativa sem dados sensíveis."""

    user_id: str
    display_name: str | None
    role: UserRole | None
    admin: bool
    deactivated: bool
    locked: bool
    suspended: bool


class AccountListResponse(BaseModel):
    """Página limitada de contas locais."""

    accounts: list[AccountAdminResponse]
    total: int
    next_token: str | None


class AccountUpdateRequest(BaseModel):
    """Campos editáveis de uma conta."""

    model_config = ConfigDict(str_strip_whitespace=False)

    display_name: str | None = Field(default=None, max_length=255)
    locked: bool | None = None

    @model_validator(mode="after")
    def require_change(self) -> AccountUpdateRequest:
        if self.display_name is None and self.locked is None:
            raise ValueError("at least one account field must be provided")
        return self


class PasswordResetRequest(BaseModel):
    """Senha nova recebida somente para encaminhamento ao Synapse."""

    new_password: SecretStr = Field(min_length=1, max_length=512)
    logout_devices: bool = True


def set_no_store(response: Response) -> None:
    """Impede armazenamento de dados administrativos."""

    response.headers.update(NO_STORE_HEADERS)


def map_synapse_admin_error(error: Exception) -> HTTPException:
    """Traduz falhas do Synapse sem expor detalhes internos."""

    if isinstance(error, SynapseUserNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
            headers=NO_STORE_HEADERS,
        )
    if isinstance(error, SynapseUserAlreadyExistsError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account already exists",
            headers=NO_STORE_HEADERS,
        )
    if isinstance(error, (SynapseAdminRateLimitedError, SynapseAdminUnavailableError)):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account administration temporarily unavailable",
            headers=NO_STORE_HEADERS,
        )
    if isinstance(error, (InvalidSynapseAdminCredentialError, SynapseAdminProtocolError)):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid response from account administration service",
            headers=NO_STORE_HEADERS,
        )
    if isinstance(error, ValueError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid account administration request",
            headers=NO_STORE_HEADERS,
        )
    raise error


def serialize_account(account: SynapseUser) -> AccountAdminResponse:
    """Serializa estado Synapse sem expor dados sensíveis."""

    return AccountAdminResponse(
        user_id=account.user_id,
        display_name=account.display_name,
        role=None,
        admin=account.admin,
        deactivated=account.deactivated,
        locked=account.locked,
        suspended=account.suspended,
    )


@router.get(
    "",
    response_model=AccountListResponse,
    summary="Lista contas locais",
)
def list_accounts(
    response: Response,
    admin: PlatformAdmin,
    service: AccountServiceDependency,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    query: str | None = Query(default=None, min_length=1, max_length=100),
) -> AccountListResponse:
    """Lista contas locais sem consultar diretamente o banco do Synapse."""

    del admin
    try:
        page = service.list(offset=offset, limit=limit, query=query)
    except Exception as error:
        raise map_synapse_admin_error(error) from None

    set_no_store(response)
    return AccountListResponse(
        accounts=[serialize_account(account) for account in page.users if not account.admin],
        total=page.total,
        next_token=page.next_token,
    )


@router.patch(
    "/{user_id}",
    response_model=AccountAdminResponse,
    summary="Atualiza uma conta local",
)
def update_account(
    user_id: str,
    payload: AccountUpdateRequest,
    response: Response,
    admin: PlatformAdmin,
    service: AccountServiceDependency,
    audit: AuditServiceDependency,
) -> AccountAdminResponse:
    """Atualiza nome de exibição e bloqueio sem entregar token administrativo ao navegador."""

    try:
        account = service.update(
            user_id=user_id,
            display_name=payload.display_name,
            locked=payload.locked,
        )
    except Exception as error:
        if payload.locked is not None:
            audit.record(
                actor_user_id=admin.identity.user_id,
                action=(
                    AuditAction.account_locked if payload.locked else AuditAction.account_unlocked
                ),
                target=user_id,
                result=AuditResult.failure,
            )
        raise map_synapse_admin_error(error) from None

    if payload.locked is not None:
        audit.record(
            actor_user_id=admin.identity.user_id,
            action=(AuditAction.account_locked if payload.locked else AuditAction.account_unlocked),
            target=user_id,
            result=AuditResult.success,
        )

    set_no_store(response)
    return serialize_account(account)


@router.post(
    "/{user_id}/password-reset",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Redefine a senha de uma conta local",
)
def reset_account_password(
    user_id: str,
    payload: PasswordResetRequest,
    response: Response,
    admin: PlatformAdmin,
    service: AccountServiceDependency,
    audit: AuditServiceDependency,
) -> None:
    """Redefine senha pelo backend sem persistir o segredo."""

    try:
        service.reset_password(
            user_id=user_id,
            new_password=payload.new_password,
            logout_devices=payload.logout_devices,
        )
    except Exception as error:
        audit.record(
            actor_user_id=admin.identity.user_id,
            action=AuditAction.password_reset,
            target=user_id,
            result=AuditResult.failure,
        )
        raise map_synapse_admin_error(error) from None
    audit.record(
        actor_user_id=admin.identity.user_id,
        action=AuditAction.password_reset,
        target=user_id,
        result=AuditResult.success,
    )
    set_no_store(response)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desativa uma conta local",
)
def deactivate_account(
    user_id: str,
    response: Response,
    admin: PlatformAdmin,
    service: AccountServiceDependency,
    audit: AuditServiceDependency,
    erase: bool = Query(default=True),
) -> None:
    """Executa exclusão lógica por desativação suportada pelo Synapse."""

    try:
        service.deactivate(user_id=user_id, erase=erase)
    except Exception as error:
        audit.record(
            actor_user_id=admin.identity.user_id,
            action=AuditAction.account_deactivated,
            target=user_id,
            result=AuditResult.failure,
        )
        raise map_synapse_admin_error(error) from None
    audit.record(
        actor_user_id=admin.identity.user_id,
        action=AuditAction.account_deactivated,
        target=user_id,
        result=AuditResult.success,
    )
    set_no_store(response)
