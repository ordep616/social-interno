"""Endpoints REST administrativos de convites."""

from datetime import datetime
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import AnyHttpUrl, BaseModel, ConfigDict

from social_internal_backend.api.dependencies import (
    NO_STORE_HEADERS,
    AppSettings,
    InvitationServiceDependency,
    PlatformAdmin,
)
from social_internal_backend.invitations import (
    InvitationConflictError,
    InvitationNotFoundError,
)
from social_internal_backend.models import Invitation, InvitationRole, InvitationStatus

router = APIRouter(prefix="/v1/admin/invitations", tags=["admin invitations"])


class InvitationCreateRequest(BaseModel):
    """Papel corporativo permitido no convite."""

    role: InvitationRole


class InvitationAdminResponse(BaseModel):
    """Representação administrativa que nunca contém segredo ou hash."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: InvitationRole
    status: InvitationStatus
    created_by: str
    created_at: datetime
    expires_at: datetime
    used_at: datetime | None
    revoked_at: datetime | None
    accepted_user_id: str | None


class InvitationCreatedResponse(InvitationAdminResponse):
    """Representação emitida uma única vez com o endereço secreto."""

    invite_url: AnyHttpUrl


def build_invite_url(base_url: AnyHttpUrl, token: str) -> str:
    """Acrescenta o token URL-safe ao prefixo público configurado."""

    return f"{str(base_url).rstrip('/')}/{quote(token, safe='')}"


def set_no_store(response: Response) -> None:
    """Impede armazenamento de respostas relacionadas a convites."""

    response.headers.update(NO_STORE_HEADERS)


def serialize_invitation(invitation: Invitation) -> InvitationAdminResponse:
    """Converte o modelo sem permitir exposição acidental de `token_hash`."""

    return InvitationAdminResponse.model_validate(invitation)


@router.post(
    "",
    response_model=InvitationCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um convite administrativo",
)
def create_invitation(
    payload: InvitationCreateRequest,
    response: Response,
    admin: PlatformAdmin,
    service: InvitationServiceDependency,
    settings: AppSettings,
) -> InvitationCreatedResponse:
    """Emite um convite e apresenta seu token somente no endereço retornado."""

    issued = service.issue(
        role=payload.role,
        created_by=admin.identity.user_id,
    )
    invitation = issued.invitation
    response.headers["Location"] = f"/v1/admin/invitations/{invitation.id}"
    set_no_store(response)
    return InvitationCreatedResponse(
        id=invitation.id,
        role=invitation.role,
        status=invitation.status,
        created_by=invitation.created_by,
        created_at=invitation.created_at,
        expires_at=invitation.expires_at,
        used_at=invitation.used_at,
        revoked_at=invitation.revoked_at,
        accepted_user_id=invitation.accepted_user_id,
        invite_url=build_invite_url(settings.invitation_public_base_url, issued.token),
    )


@router.get(
    "",
    response_model=list[InvitationAdminResponse],
    summary="Lista convites administrativos",
)
def list_invitations(
    response: Response,
    admin: PlatformAdmin,
    service: InvitationServiceDependency,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[InvitationAdminResponse]:
    """Lista convites com paginação limitada e sem segredos."""

    del admin
    set_no_store(response)
    return [
        serialize_invitation(invitation) for invitation in service.list(offset=offset, limit=limit)
    ]


@router.get(
    "/{invitation_id}",
    response_model=InvitationAdminResponse,
    summary="Consulta um convite administrativo",
)
def get_invitation(
    invitation_id: UUID,
    response: Response,
    admin: PlatformAdmin,
    service: InvitationServiceDependency,
) -> InvitationAdminResponse:
    """Consulta um convite pelo identificador público."""

    del admin
    try:
        invitation = service.get(invitation_id)
    except InvitationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
            headers=NO_STORE_HEADERS,
        ) from None
    set_no_store(response)
    return serialize_invitation(invitation)


@router.delete(
    "/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoga um convite administrativo",
)
def revoke_invitation(
    invitation_id: UUID,
    response: Response,
    admin: PlatformAdmin,
    service: InvitationServiceDependency,
) -> None:
    """Realiza revogação lógica idempotente quando o estado permite."""

    del admin
    try:
        service.revoke(invitation_id)
    except InvitationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
            headers=NO_STORE_HEADERS,
        ) from None
    except InvitationConflictError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invitation cannot be revoked in its current state",
            headers=NO_STORE_HEADERS,
        ) from None
    set_no_store(response)
