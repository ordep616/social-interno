"""Persistência das tentativas duráveis de cadastro."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from social_internal_backend.models import RegistrationAttempt, RegistrationAttemptStatus

ACTIVE_ATTEMPT_STATUSES = (
    RegistrationAttemptStatus.processing,
    RegistrationAttemptStatus.synapse_created,
    RegistrationAttemptStatus.reconciliation_required,
)


class RegistrationAttemptRepository:
    """Executa consultas e transições sem controlar a transação externa."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, attempt: RegistrationAttempt) -> RegistrationAttempt:
        """Adiciona e materializa uma tentativa na transação atual."""

        self._session.add(attempt)
        self._session.flush()
        return attempt

    def get(self, attempt_id: UUID) -> RegistrationAttempt | None:
        """Busca uma tentativa pelo identificador operacional."""

        return self._session.get(RegistrationAttempt, attempt_id)

    def get_active_by_invitation(
        self,
        invitation_id: UUID,
    ) -> RegistrationAttempt | None:
        """Obtém a tentativa ativa exclusiva de um convite."""

        statement = select(RegistrationAttempt).where(
            RegistrationAttempt.invitation_id == invitation_id,
            RegistrationAttempt.status.in_(ACTIVE_ATTEMPT_STATUSES),
        )
        return self._session.scalars(statement).one_or_none()

    def get_active_by_matrix_user_id(
        self,
        matrix_user_id: str,
    ) -> RegistrationAttempt | None:
        """Obtém a tentativa ativa exclusiva de uma identidade Matrix."""

        statement = select(RegistrationAttempt).where(
            RegistrationAttempt.matrix_user_id == matrix_user_id,
            RegistrationAttempt.status.in_(ACTIVE_ATTEMPT_STATUSES),
        )
        return self._session.scalars(statement).one_or_none()

    def mark_synapse_created(
        self,
        attempt_id: UUID,
        now: datetime,
    ) -> RegistrationAttempt | None:
        """Confirma `201` somente para uma tentativa em processamento."""

        statement = (
            update(RegistrationAttempt)
            .where(
                RegistrationAttempt.id == attempt_id,
                RegistrationAttempt.status == RegistrationAttemptStatus.processing,
            )
            .values(
                status=RegistrationAttemptStatus.synapse_created,
                updated_at=now,
                failure_code=None,
            )
            .returning(RegistrationAttempt)
        )
        return self._session.execute(statement).scalar_one_or_none()

    def mark_completed(
        self,
        attempt_id: UUID,
        now: datetime,
    ) -> RegistrationAttempt | None:
        """Conclui somente uma tentativa com criação confirmada."""

        statement = (
            update(RegistrationAttempt)
            .where(
                RegistrationAttempt.id == attempt_id,
                RegistrationAttempt.status == RegistrationAttemptStatus.synapse_created,
            )
            .values(
                status=RegistrationAttemptStatus.completed,
                updated_at=now,
                completed_at=now,
                failure_code=None,
            )
            .returning(RegistrationAttempt)
        )
        return self._session.execute(statement).scalar_one_or_none()

    def mark_released(
        self,
        attempt_id: UUID,
        *,
        failure_code: str,
        now: datetime,
    ) -> RegistrationAttempt | None:
        """Libera somente uma tentativa que ainda não alcançou o `PUT`."""

        statement = (
            update(RegistrationAttempt)
            .where(
                RegistrationAttempt.id == attempt_id,
                RegistrationAttempt.status == RegistrationAttemptStatus.processing,
            )
            .values(
                status=RegistrationAttemptStatus.released,
                updated_at=now,
                completed_at=None,
                failure_code=failure_code,
            )
            .returning(RegistrationAttempt)
        )
        return self._session.execute(statement).scalar_one_or_none()

    def mark_reconciliation_required(
        self,
        attempt_id: UUID,
        *,
        failure_code: str,
        now: datetime,
    ) -> RegistrationAttempt | None:
        """Isola resultado ambíguo sem permitir nova criação automática."""

        statement = (
            update(RegistrationAttempt)
            .where(
                RegistrationAttempt.id == attempt_id,
                RegistrationAttempt.status.in_(
                    (
                        RegistrationAttemptStatus.processing,
                        RegistrationAttemptStatus.synapse_created,
                    )
                ),
            )
            .values(
                status=RegistrationAttemptStatus.reconciliation_required,
                updated_at=now,
                completed_at=None,
                failure_code=failure_code,
            )
            .returning(RegistrationAttempt)
        )
        return self._session.execute(statement).scalar_one_or_none()
