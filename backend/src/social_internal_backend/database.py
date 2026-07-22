"""Primitivas de acesso ao PostgreSQL próprio do serviço."""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from social_internal_backend.settings import Settings


class Base(DeclarativeBase):
    """Metadados compartilhados pelos modelos do serviço."""


def build_engine(settings: Settings) -> Engine:
    """Cria um engine sem abrir conexão antecipadamente."""

    return create_engine(str(settings.database_url), pool_pre_ping=True)


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Cria sessões transacionais para o PostgreSQL próprio."""

    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
