"""Dependências HTTP do serviço administrativo."""

from collections.abc import Iterator
from typing import Annotated, cast

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, sessionmaker

from social_internal_backend.authorization import (
    AuthorizedPlatformAdmin,
    CorporateUserAccessDeniedError,
    PlatformAdminAccessDeniedError,
    PlatformAdminAuthorizationService,
    UserCapabilitiesContext,
    UserCapabilitiesService,
    UserRoleAssignmentRepository,
)
from social_internal_backend.invitations import InvitationService
from social_internal_backend.settings import Settings
from social_internal_backend.synapse import (
    InvalidMatrixAccessTokenError,
    SynapseClient,
    SynapseProtocolError,
    SynapseRateLimitedError,
    SynapseUnavailableError,
)

NO_STORE_HEADERS = {"Cache-Control": "no-store"}
BEARER_CHALLENGE_HEADERS = {
    **NO_STORE_HEADERS,
    "WWW-Authenticate": "Bearer",
}

bearer_scheme = HTTPBearer(auto_error=False)


def get_database_session(request: Request) -> Iterator[Session]:
    """Abre uma sessão do banco próprio durante uma única requisição."""

    factory = cast(sessionmaker[Session], request.app.state.session_factory)
    with factory() as session:
        yield session


DatabaseSession = Annotated[Session, Depends(get_database_session)]


def get_app_settings(request: Request) -> Settings:
    """Obtém a configuração validada associada à aplicação."""

    return cast(Settings, request.app.state.settings)


AppSettings = Annotated[Settings, Depends(get_app_settings)]


def get_invitation_service(session: DatabaseSession) -> InvitationService:
    """Monta as regras de convite sobre a sessão da requisição."""

    return InvitationService(session)


InvitationServiceDependency = Annotated[InvitationService, Depends(get_invitation_service)]


def get_platform_admin_authorization_service(
    settings: AppSettings,
    session: DatabaseSession,
) -> Iterator[PlatformAdminAuthorizationService]:
    """Monta e encerra o cliente usado para validar a credencial Matrix."""

    with SynapseClient(
        base_url=str(settings.synapse_base_url),
        timeout_seconds=settings.synapse_request_timeout_seconds,
    ) as client:
        yield PlatformAdminAuthorizationService(
            identity_provider=client,
            role_repository=UserRoleAssignmentRepository(session),
        )


PlatformAdminAuthorization = Annotated[
    PlatformAdminAuthorizationService,
    Depends(get_platform_admin_authorization_service),
]


def get_user_capabilities_service(
    settings: AppSettings,
    session: DatabaseSession,
) -> Iterator[UserCapabilitiesService]:
    """Monta e encerra o cliente usado para resolver capacidades corporativas."""

    with SynapseClient(
        base_url=str(settings.synapse_base_url),
        timeout_seconds=settings.synapse_request_timeout_seconds,
    ) as client:
        yield UserCapabilitiesService(
            identity_provider=client,
            role_repository=UserRoleAssignmentRepository(session),
        )


UserCapabilities = Annotated[
    UserCapabilitiesService,
    Depends(get_user_capabilities_service),
]
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]


def require_platform_admin(
    credentials: BearerCredentials,
    authorization: PlatformAdminAuthorization,
) -> AuthorizedPlatformAdmin:
    """Exige uma sessão Matrix válida associada a um `platform_admin` local."""

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Matrix authentication required",
            headers=BEARER_CHALLENGE_HEADERS,
        )

    try:
        return authorization.authorize(credentials.credentials)
    except InvalidMatrixAccessTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Matrix authentication",
            headers=BEARER_CHALLENGE_HEADERS,
        ) from None
    except PlatformAdminAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform administrator role required",
            headers=NO_STORE_HEADERS,
        ) from None
    except SynapseRateLimitedError, SynapseUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Matrix authentication temporarily unavailable",
            headers=NO_STORE_HEADERS,
        ) from None
    except SynapseProtocolError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid response from Matrix authentication service",
            headers=NO_STORE_HEADERS,
        ) from None


PlatformAdmin = Annotated[AuthorizedPlatformAdmin, Depends(require_platform_admin)]


def require_user_capabilities(
    credentials: BearerCredentials,
    service: UserCapabilities,
) -> UserCapabilitiesContext:
    """Exige sessão Matrix válida associada a um papel corporativo local."""

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Matrix authentication required",
            headers=BEARER_CHALLENGE_HEADERS,
        )

    try:
        return service.resolve(credentials.credentials)
    except InvalidMatrixAccessTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Matrix authentication",
            headers=BEARER_CHALLENGE_HEADERS,
        ) from None
    except CorporateUserAccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Corporate user role required",
            headers=NO_STORE_HEADERS,
        ) from None
    except SynapseRateLimitedError, SynapseUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Matrix authentication temporarily unavailable",
            headers=NO_STORE_HEADERS,
        ) from None
    except SynapseProtocolError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid response from Matrix authentication service",
            headers=NO_STORE_HEADERS,
        ) from None


CurrentUserCapabilities = Annotated[
    UserCapabilitiesContext,
    Depends(require_user_capabilities),
]
