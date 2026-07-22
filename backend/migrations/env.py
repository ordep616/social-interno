"""Ambiente de migrações do banco próprio do serviço."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection

from social_internal_backend import models
from social_internal_backend.database import build_engine
from social_internal_backend.settings import get_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = models.Invitation.metadata


def run_migrations_offline() -> None:
    """Gera SQL sem abrir uma conexão com o PostgreSQL."""

    context.configure(
        url=str(get_settings().database_url),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def execute_migrations(connection: Connection) -> None:
    """Executa migrações usando uma conexão existente."""

    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Executa migrações conectando ao PostgreSQL configurado."""

    engine = build_engine(get_settings())
    try:
        with engine.connect() as connection:
            execute_migrations(connection)
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
