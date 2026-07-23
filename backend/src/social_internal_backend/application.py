"""Fábrica da aplicação FastAPI."""

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import RequestResponseEndpoint

from social_internal_backend.api.admin_invitations import router as admin_invitations_router
from social_internal_backend.api.dependencies import NO_STORE_HEADERS
from social_internal_backend.api.health import router as health_router
from social_internal_backend.database import build_engine, build_session_factory
from social_internal_backend.settings import Settings, get_settings

ADMIN_INVITATIONS_PATH = "/v1/admin/invitations"


async def add_admin_invitation_cache_control(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    """Aplica `no-store` inclusive às respostas automáticas de validação."""

    response = await call_next(request)
    if request.url.path == ADMIN_INVITATIONS_PATH or request.url.path.startswith(
        f"{ADMIN_INVITATIONS_PATH}/"
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
    app.middleware("http")(add_admin_invitation_cache_control)
    app.include_router(health_router)
    app.include_router(admin_invitations_router)
    return app
