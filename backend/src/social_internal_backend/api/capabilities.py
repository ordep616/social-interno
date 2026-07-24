"""Capacidades corporativas da identidade autenticada."""

from fastapi import APIRouter, Response
from pydantic import BaseModel

from social_internal_backend.api.dependencies import (
    NO_STORE_HEADERS,
    CurrentUserCapabilities,
)
from social_internal_backend.models import UserRole

router = APIRouter(prefix="/v1/me", tags=["current user"])


class UserActivationCapabilitiesResponse(BaseModel):
    """Operações corporativas liberadas para a identidade."""

    can_manage_user_activations: bool


class CurrentUserCapabilitiesResponse(BaseModel):
    """Identidade, papel próprio e capacidades calculadas pelo backend."""

    user_id: str
    role: UserRole
    capabilities: UserActivationCapabilitiesResponse


@router.get(
    "/capabilities",
    response_model=CurrentUserCapabilitiesResponse,
    summary="Consulta as capacidades corporativas da identidade atual",
)
def get_current_user_capabilities(
    response: Response,
    current_user: CurrentUserCapabilities,
) -> CurrentUserCapabilitiesResponse:
    """Retorna capacidades sem substituir a autorização de cada operação."""

    response.headers.update(NO_STORE_HEADERS)
    return CurrentUserCapabilitiesResponse(
        user_id=current_user.identity.user_id,
        role=current_user.assignment.role,
        capabilities=UserActivationCapabilitiesResponse(
            can_manage_user_activations=current_user.can_manage_user_activations,
        ),
    )
