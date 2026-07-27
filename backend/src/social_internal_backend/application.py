"""Fábrica da aplicação FastAPI."""

from typing import cast

from fastapi import FastAPI, Request, Response, status
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import RequestResponseEndpoint
from starlette.types import ExceptionHandler

from social_internal_backend.api.activation_validations import (
    router as activation_validations_router,
)
from social_internal_backend.api.admin_accounts import router as admin_accounts_router
from social_internal_backend.api.admin_invitations import router as admin_invitations_router
from social_internal_backend.api.capabilities import router as capabilities_router
from social_internal_backend.api.dependencies import NO_STORE_HEADERS
from social_internal_backend.api.health import router as health_router
from social_internal_backend.api.registrations import router as registrations_router
from social_internal_backend.database import build_engine, build_session_factory
from social_internal_backend.settings import Settings, get_settings

ADMIN_INVITATIONS_PATH = "/v1/admin/invitations"
ADMIN_ACCOUNTS_PATH = "/v1/admin/accounts"
CURRENT_USER_CAPABILITIES_PATH = "/v1/me/capabilities"
ACTIVATION_VALIDATIONS_PATH = "/v1/activation-validations"
REGISTRATIONS_PATH = "/v1/registrations"

ACTIVATION_ERROR_CODES = {
    status.HTTP_404_NOT_FOUND: "activation_not_found",
    status.HTTP_409_CONFLICT: "activation_conflict",
    status.HTTP_410_GONE: "activation_unavailable",
    status.HTTP_422_UNPROCESSABLE_CONTENT: "invalid_request",
    status.HTTP_429_TOO_MANY_REQUESTS: "rate_limited",
    status.HTTP_502_BAD_GATEWAY: "upstream_invalid_response",
    status.HTTP_503_SERVICE_UNAVAILABLE: "service_unavailable",
}


def is_activation_validation_path(path: str) -> bool:
    """Inclui o redirecionamento automático da variante com barra final."""

    return path in {
        ACTIVATION_VALIDATIONS_PATH,
        f"{ACTIVATION_VALIDATIONS_PATH}/",
        REGISTRATIONS_PATH,
        f"{REGISTRATIONS_PATH}/",
    }


def activation_error_response(
    status_code: int,
    error_code: str,
    *,
    retry_after: str | None = None,
) -> JSONResponse:
    """Retorna o envelope mínimo sem ecoar entrada ou detalhe interno."""

    headers = dict(NO_STORE_HEADERS)
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": error_code}},
        headers=headers,
    )


async def handle_http_exception(
    request: Request,
    exception: StarletteHTTPException,
) -> Response:
    """Sanitiza somente os erros conhecidos da pré-validação."""

    if is_activation_validation_path(request.url.path):
        error_code = ACTIVATION_ERROR_CODES.get(exception.status_code)
        if error_code is not None:
            retry_after = (
                exception.headers.get("Retry-After") if exception.headers is not None else None
            )
            error_code = (
                exception.headers.get("X-Activation-Error-Code", error_code)
                if exception.headers is not None
                else error_code
            )
            return activation_error_response(
                exception.status_code,
                error_code,
                retry_after=retry_after,
            )
    return await http_exception_handler(request, exception)


async def handle_request_validation_error(
    request: Request,
    exception: RequestValidationError,
) -> Response:
    """Impede o `422` automático de repetir token ou corpo inválido."""

    if is_activation_validation_path(request.url.path):
        return activation_error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "invalid_request",
        )
    return await request_validation_exception_handler(request, exception)


async def add_sensitive_response_cache_control(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    """Aplica `no-store` inclusive às respostas automáticas e de erro."""

    try:
        response = await call_next(request)
    except Exception:
        if is_activation_validation_path(request.url.path):
            return activation_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "service_unavailable",
            )
        raise
    if (
        is_activation_validation_path(request.url.path)
        or request.url.path == CURRENT_USER_CAPABILITIES_PATH
        or request.url.path == ADMIN_INVITATIONS_PATH
        or request.url.path.startswith(f"{ADMIN_INVITATIONS_PATH}/")
        or request.url.path == ADMIN_ACCOUNTS_PATH
        or request.url.path.startswith(f"{ADMIN_ACCOUNTS_PATH}/")
    ):
        response.headers.update(NO_STORE_HEADERS)
    return response


def create_app(settings: Settings | None = None) -> FastAPI:
    """Monta a aplicação sem conectar a serviços externos."""

    resolved_settings = settings or get_settings()
    app = FastAPI(
        title="Social Interno Backend",
        version="0.1.0",
        description="Serviço auxiliar de convites e ciclo de vida de contas.",
    )
    engine = build_engine(resolved_settings)
    app.state.settings = resolved_settings
    app.state.engine = engine
    app.state.session_factory = build_session_factory(engine)
    app.add_exception_handler(
        StarletteHTTPException,
        cast(ExceptionHandler, handle_http_exception),
    )
    app.add_exception_handler(
        RequestValidationError,
        cast(ExceptionHandler, handle_request_validation_error),
    )
    if resolved_settings.cors_allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(resolved_settings.cors_allowed_origins),
            allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type"],
        )
    app.middleware("http")(add_sensitive_response_cache_control)
    app.include_router(health_router)
    app.include_router(activation_validations_router)
    app.include_router(registrations_router)
    app.include_router(capabilities_router)
    app.include_router(admin_invitations_router)
    app.include_router(admin_accounts_router)
    return app
