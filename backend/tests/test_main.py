"""Ponto de entrada ASGI."""

import importlib
import sys
from typing import cast

import pytest
from fastapi import FastAPI

from social_internal_backend.settings import get_settings


def test_main_exposes_fastapi_app(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BACKEND_ENVIRONMENT", "test")
    monkeypatch.setenv(
        "BACKEND_DATABASE_URL",
        "postgresql+psycopg://test:test@127.0.0.1:5433/test",
    )
    monkeypatch.setenv("BACKEND_SYNAPSE_BASE_URL", "http://127.0.0.1:8008")
    monkeypatch.setenv(
        "BACKEND_INVITATION_PUBLIC_BASE_URL",
        "http://127.0.0.1:8080/register",
    )
    get_settings.cache_clear()
    sys.modules.pop("social_internal_backend.main", None)

    module = importlib.import_module("social_internal_backend.main")
    app = cast(FastAPI, module.app)

    assert app.title == "Social Interno Backend"
    get_settings.cache_clear()
