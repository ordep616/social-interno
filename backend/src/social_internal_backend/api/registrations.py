"""Endpoint público de criação da conta previamente autorizada."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field, SecretStr

from social_internal_backend.api.dependencies import RegistrationServiceDependency
from social_internal_backend.registrations import (
    RegistrationConflictError,
    RegistrationNotFoundError,
    RegistrationPasswordPolicyError,
    RegistrationRateLimitedError,
    RegistrationStorageUnavailableError,
    RegistrationUnavailableError,
    RegistrationUpstreamInvalidResponseError,
    RegistrationUpstreamUnavailableError,
)

router = APIRouter(prefix="/v1/registrations", tags=["activations"])


class RegistrationRequest(BaseModel):
    """Segredos omitidos de representações e respostas."""

    model_config = ConfigDict(extra="forbid")
    invitation_token: Annotated[SecretStr, Field(min_length=1, max_length=512)]
    password: Annotated[SecretStr, Field(min_length=15, max_length=128)]


class RegistrationResponse(BaseModel):
    user_id: str


def public_error(
    status_code: int,
    *,
    error_code: str | None = None,
    retry_after_seconds: int | None = None,
) -> HTTPException:
    headers: dict[str, str] = {}
    if error_code is not None:
        headers["X-Activation-Error-Code"] = error_code
    if retry_after_seconds is not None:
        headers["Retry-After"] = str(retry_after_seconds)
    return HTTPException(
        status_code=status_code,
        detail="Registration request failed",
        headers=headers or None,
    )


@router.post("", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegistrationRequest,
    request: Request,
    service: RegistrationServiceDependency,
) -> RegistrationResponse:
    if request.url.query:
        raise public_error(status.HTTP_422_UNPROCESSABLE_CONTENT)
    invitation_token = payload.invitation_token.get_secret_value()
    try:
        result = service.register(invitation_token, payload.password)
    except RegistrationNotFoundError:
        raise public_error(status.HTTP_404_NOT_FOUND) from None
    except RegistrationUnavailableError:
        raise public_error(status.HTTP_410_GONE) from None
    except RegistrationConflictError:
        raise public_error(status.HTTP_409_CONFLICT) from None
    except RegistrationPasswordPolicyError:
        raise public_error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            error_code="password_policy_violation",
        ) from None
    except RegistrationRateLimitedError as error:
        raise public_error(
            status.HTTP_429_TOO_MANY_REQUESTS,
            retry_after_seconds=error.retry_after_seconds,
        ) from None
    except RegistrationStorageUnavailableError, RegistrationUpstreamUnavailableError:
        raise public_error(status.HTTP_503_SERVICE_UNAVAILABLE) from None
    except RegistrationUpstreamInvalidResponseError:
        raise public_error(status.HTTP_502_BAD_GATEWAY) from None
    finally:
        del invitation_token
    return RegistrationResponse(user_id=result.user_id)
