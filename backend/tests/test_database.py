"""Preparação do acesso ao PostgreSQL sem abrir conexão de rede."""

from sqlalchemy.orm import Session

from social_internal_backend.database import build_engine, build_session_factory
from social_internal_backend.settings import Settings


def test_builds_psycopg_engine_and_session_factory(settings: Settings) -> None:
    engine = build_engine(settings)
    session_factory = build_session_factory(engine)

    try:
        assert engine.url.drivername == "postgresql+psycopg"
        with session_factory() as session:
            assert isinstance(session, Session)
    finally:
        engine.dispose()
