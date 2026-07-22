"""Fábrica da aplicação FastAPI."""

from fastapi import FastAPI

from social_internal_backend.api.health import router as health_router
from social_internal_backend.settings import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Monta a aplicação sem conectar a serviços externos."""

    resolved_settings = settings or get_settings()
    app = FastAPI(
        title="Social Interno Backend",
        version="0.1.0",
        description="Serviço auxiliar de convites e ciclo de vida de contas.",
    )
    app.state.settings = resolved_settings
    app.include_router(health_router)
    return app
