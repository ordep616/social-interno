"""Endpoint público e somente leitura de pré-validação da ativação."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field, SecretStr

from social_internal_backend.activations import (
    ActivationValidationConflictError,
    ActivationValidationNotFoundError,
    ActivationValidationRateLimitedError,
    ActivationValidationStorageUnavailableError,
    ActivationValidationUnavailableError,
)
from social_internal_backend.api.dependencies import ActivationValidationServiceDependency
from social_internal_backend.models import InvitationRole
from social_internal_backend.synapse import (
    InvalidSynapseAdminCredentialError,
    SynapseAdminProtocolError,
    SynapseAdminRateLimitedError,
    SynapseAdminUnavailableError,
)

router = APIRouter(prefix="/v1/activation-validations", tags=["activations"])


class ActivationValidationRequest(BaseModel):
    """Segredo de posse enviado somente no corpo e omitido de representações."""

    model_config = ConfigDict(extra="forbid")

    invitation_token: Annotated[SecretStr, Field(min_length=1, max_length=512)]


class ActivationValidationResponse(BaseModel):
    """Identidade imutável definida previamente pelo administrador."""

    target_user_id: str
    username: str
    role: InvitationRole
    expires_at: datetime


def public_error(status_code: int, *, retry_after_seconds: int | None = None) -> HTTPException:
    """Cria um erro cuja mensagem interna será substituída pelo handler público."""

    headers = {"Retry-After": str(retry_after_seconds)} if retry_after_seconds is not None else None
    return HTTPException(
        status_code=status_code, detail="Activation request failed", headers=headers
    )


@router.post(
    "",
    response_model=ActivationValidationResponse,
    summary="Pré-valida uma identidade previamente autorizada",
)
def validate_activation(
    payload: ActivationValidationRequest,
    request: Request,
    service: ActivationValidationServiceDependency,
) -> ActivationValidationResponse:
    """Consulta convite e identidade sem reservar, consumir ou criar conta."""

    if request.url.query:
        raise public_error(status.HTTP_422_UNPROCESSABLE_CONTENT)

    invitation_token = payload.invitation_token.get_secret_value()
    try:
        result = service.validate(invitation_token)
    except ActivationValidationNotFoundError:
        raise public_error(status.HTTP_404_NOT_FOUND) from None
    except ActivationValidationUnavailableError:
        raise public_error(status.HTTP_410_GONE) from None
    except ActivationValidationConflictError:
        raise public_error(status.HTTP_409_CONFLICT) from None
    except ActivationValidationRateLimitedError as error:
        raise public_error(
            status.HTTP_429_TOO_MANY_REQUESTS,
            retry_after_seconds=error.retry_after_seconds,
        ) from None
    except ActivationValidationStorageUnavailableError:
        raise public_error(status.HTTP_503_SERVICE_UNAVAILABLE) from None
    except SynapseAdminRateLimitedError:
        raise public_error(status.HTTP_503_SERVICE_UNAVAILABLE) from None
    except SynapseAdminProtocolError:
        raise public_error(status.HTTP_502_BAD_GATEWAY) from None
    except InvalidSynapseAdminCredentialError, SynapseAdminUnavailableError:
        raise public_error(status.HTTP_503_SERVICE_UNAVAILABLE) from None
    finally:
        del invitation_token

    return ActivationValidationResponse(
        target_user_id=result.target_user_id,
        username=result.username,
        role=result.role,
        expires_at=result.expires_at,
    )
