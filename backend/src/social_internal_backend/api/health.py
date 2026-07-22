"""Endpoint de vivacidade sem dependências externas."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Resposta estável do endpoint de vivacidade."""

    status: Literal["ok"] = "ok"


@router.get("/health", response_model=HealthResponse, summary="Verifica a vivacidade")
def health() -> HealthResponse:
    """Confirma que o processo HTTP está respondendo."""

    return HealthResponse()
