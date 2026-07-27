"""Remove contadores de ativação após a retenção operacional aprovada."""

import sys
from datetime import UTC, datetime

from sqlalchemy.exc import SQLAlchemyError

from social_internal_backend.database import build_engine, build_session_factory
from social_internal_backend.rate_limits import ActivationRateLimitRepository
from social_internal_backend.settings import get_settings


def main() -> int:
    """Executa uma limpeza idempotente sem receber token ou outro segredo."""

    engine = build_engine(get_settings())
    session_factory = build_session_factory(engine)
    try:
        with session_factory.begin() as session:
            deleted_count = ActivationRateLimitRepository(session).delete_expired(
                now=datetime.now(UTC)
            )
    except SQLAlchemyError:
        print("Falha ao limpar os limites de ativação.", file=sys.stderr)
        return 1
    finally:
        engine.dispose()

    print(f"Contadores de ativação removidos: {deleted_count}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
