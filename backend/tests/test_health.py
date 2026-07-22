"""Contrato mínimo de vivacidade."""

import httpx
import pytest


@pytest.mark.anyio
async def test_health_returns_ok(client: httpx.AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_health_is_documented(client: httpx.AsyncClient) -> None:
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    assert "/health" in response.json()["paths"]
