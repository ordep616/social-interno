"""Persistência e transições atômicas de convites."""

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import case, select, update
from sqlalchemy.orm import Session

from social_internal_backend.models import Invitation, InvitationStatus


class InvitationRepository:
    """Acessa convites usando exclusivamente o banco próprio do serviço."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, invitation: Invitation) -> Invitation:
        """Adiciona e materializa o convite na transação atual."""

        self._session.add(invitation)
        self._session.flush()
        return invitation

    def get(self, invitation_id: UUID) -> Invitation | None:
        """Busca um convite pelo identificador administrativo."""

        return self._session.get(Invitation, invitation_id)

    def get_by_token_hash(self, token_hash: str) -> Invitation | None:
        """Busca um convite pelo hash, nunca pelo token aberto."""

        statement = select(Invitation).where(Invitation.token_hash == token_hash)
        return self._session.scalars(statement).one_or_none()

    def list(self, *, offset: int = 0, limit: int = 100) -> Sequence[Invitation]:
        """Lista convites recentes de forma determinística e limitada."""

        statement = (
            select(Invitation)
            .order_by(Invitation.created_at.desc(), Invitation.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return self._session.scalars(statement).all()

    def claim_pending(self, token_hash: str, now: datetime) -> Invitation | None:
        """Move um convite válido para processamento em uma única instrução."""

        statement = (
            update(Invitation)
            .where(
                Invitation.token_hash == token_hash,
                Invitation.status == InvitationStatus.pending,
                Invitation.expires_at > now,
            )
            .values(status=InvitationStatus.processing)
            .returning(Invitation)
        )
        return self._session.execute(statement).scalar_one_or_none()

    def expire_pending(self, token_hash: str, now: datetime) -> Invitation | None:
        """Materializa a expiração quando uma aceitação encontra o prazo vencido."""

        statement = (
            update(Invitation)
            .where(
                Invitation.token_hash == token_hash,
                Invitation.status == InvitationStatus.pending,
                Invitation.expires_at <= now,
            )
            .values(status=InvitationStatus.expired)
            .returning(Invitation)
        )
        return self._session.execute(statement).scalar_one_or_none()

    def revoke_pending(self, invitation_id: UUID, now: datetime) -> Invitation | None:
        """Revoga somente um convite ainda pendente, protegendo contra corrida."""

        statement = (
            update(Invitation)
            .where(
                Invitation.id == invitation_id,
                Invitation.status == InvitationStatus.pending,
            )
            .values(status=InvitationStatus.revoked, revoked_at=now)
            .returning(Invitation)
        )
        return self._session.execute(statement).scalar_one_or_none()

    def complete_processing(
        self,
        invitation_id: UUID,
        accepted_user_id: str,
        now: datetime,
    ) -> Invitation | None:
        """Conclui atomicamente um convite previamente reservado."""

        statement = (
            update(Invitation)
            .where(
                Invitation.id == invitation_id,
                Invitation.status == InvitationStatus.processing,
            )
            .values(
                status=InvitationStatus.used,
                used_at=now,
                accepted_user_id=accepted_user_id,
            )
            .returning(Invitation)
        )
        return self._session.execute(statement).scalar_one_or_none()

    def release_processing(self, invitation_id: UUID, now: datetime) -> Invitation | None:
        """Libera uma reserva falha ou a expira caso o prazo tenha terminado."""

        next_status = case(
            (Invitation.expires_at <= now, InvitationStatus.expired),
            else_=InvitationStatus.pending,
        )
        statement = (
            update(Invitation)
            .where(
                Invitation.id == invitation_id,
                Invitation.status == InvitationStatus.processing,
            )
            .values(status=next_status)
            .returning(Invitation)
        )
        return self._session.execute(statement).scalar_one_or_none()
