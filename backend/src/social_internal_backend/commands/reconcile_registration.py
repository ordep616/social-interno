"""Comando local para reconciliar uma sessão de provisionamento conhecida."""

import argparse
import sys
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from social_internal_backend.database import build_engine, build_session_factory
from social_internal_backend.registrations import (
    ReconciliationDeviceStillPresentError,
    ReconciliationNotFoundError,
    ReconciliationStateError,
    RegistrationReconciliationService,
)
from social_internal_backend.settings import get_settings
from social_internal_backend.synapse import (
    InvalidSynapseAdminCredentialError,
    SynapseAdminClient,
    SynapseAdminProtocolError,
    SynapseAdminRateLimitedError,
    SynapseAdminUnavailableError,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Revoga o dispositivo conhecido e conclui uma ativação bloqueada.",
    )
    parser.add_argument("attempt_id", type=UUID, help="UUID da tentativa operacional")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    engine = build_engine(settings)
    session_factory = build_session_factory(engine)
    try:
        with (
            SynapseAdminClient(
                base_url=str(settings.synapse_base_url),
                timeout_seconds=settings.synapse_request_timeout_seconds,
                matrix_server_name=settings.matrix_server_name,
                admin_access_token=settings.synapse_admin_access_token,
            ) as admin_client,
            session_factory() as session,
        ):
            result = RegistrationReconciliationService(
                session,
                admin_provider=admin_client,
            ).reconcile(args.attempt_id)
    except ReconciliationNotFoundError:
        print("Tentativa não encontrada.", file=sys.stderr)
        return 1
    except ReconciliationStateError:
        print(
            "Tentativa sem estado ou dispositivo suficiente para reconciliação automática.",
            file=sys.stderr,
        )
        return 2
    except ReconciliationDeviceStillPresentError:
        print("O dispositivo de provisionamento continua presente.", file=sys.stderr)
        return 3
    except (
        InvalidSynapseAdminCredentialError,
        SynapseAdminProtocolError,
        SynapseAdminRateLimitedError,
        SynapseAdminUnavailableError,
    ):
        print("Não foi possível confirmar a revogação no Synapse.", file=sys.stderr)
        return 4
    except SQLAlchemyError:
        print("Falha ao acessar o banco próprio do serviço.", file=sys.stderr)
        return 5
    finally:
        engine.dispose()

    state = "revogado agora" if result.device_was_present else "já ausente"
    print(f"Ativação concluída para {result.user_id}; dispositivo {state}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
