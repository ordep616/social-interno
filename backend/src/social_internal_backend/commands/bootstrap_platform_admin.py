"""Comando local para inicializar o primeiro administrador da plataforma."""

import argparse
import sys
from collections.abc import Sequence

from sqlalchemy.exc import SQLAlchemyError

from social_internal_backend.authorization import (
    BootstrapAlreadyCompletedError,
    PlatformAdminBootstrapService,
)
from social_internal_backend.database import build_engine, build_session_factory
from social_internal_backend.settings import get_settings


def build_parser() -> argparse.ArgumentParser:
    """Define a interface sem aceitar senha ou qualquer token."""

    parser = argparse.ArgumentParser(
        description="Atribui platform_admin à primeira identidade Matrix da instalação.",
    )
    parser.add_argument("matrix_user_id", help="Identidade completa, por exemplo @admin:localhost")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Executa o bootstrap usando apenas configuração local do servidor."""

    args = build_parser().parse_args(argv)
    engine = build_engine(get_settings())
    session_factory = build_session_factory(engine)
    try:
        with session_factory() as session:
            result = PlatformAdminBootstrapService(session).bootstrap(args.matrix_user_id)
    except ValueError:
        print("Identidade Matrix inválida.", file=sys.stderr)
        return 2
    except BootstrapAlreadyCompletedError:
        print("Bootstrap já concluído para outra identidade Matrix.", file=sys.stderr)
        return 1
    except SQLAlchemyError:
        print("Falha ao acessar o banco próprio do serviço.", file=sys.stderr)
        return 3
    finally:
        engine.dispose()

    state = "criada" if result.created else "já existente"
    print(f"Atribuição platform_admin {state} para {result.assignment.matrix_user_id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
