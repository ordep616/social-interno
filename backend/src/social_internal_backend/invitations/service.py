"""Regras de negócio do ciclo de vida dos convites."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID

from sqlalchemy.orm import Session

from social_internal_backend.invitations.repository import InvitationRepository
from social_internal_backend.invitations.tokens import (
    generate_invitation_token,
    hash_invitation_token,
)
from social_internal_backend.models import Invitation, InvitationRole, InvitationStatus

INVITATION_LIFETIME = timedelta(hours=24)
DEFAULT_LIST_LIMIT = 100
MAX_LIST_LIMIT = 100

Clock = Callable[[], datetime]
TokenFactory = Callable[[], str]


class InvitationRepositoryPort(Protocol):
    """Operações de persistência exigidas pelas regras de negócio."""

    def add(self, invitation: Invitation) -> Invitation: ...

    def get(self, invitation_id: UUID) -> Invitation | None: ...

    def get_by_token_hash(self, token_hash: str) -> Invitation | None: ...

    def list(self, *, offset: int = 0, limit: int = 100) -> Sequence[Invitation]: ...

    def claim_pending(self, token_hash: str, now: datetime) -> Invitation | None: ...

    def expire_pending(self, token_hash: str, now: datetime) -> Invitation | None: ...

    def revoke_pending(self, invitation_id: UUID, now: datetime) -> Invitation | None: ...

    def complete_processing(
        self,
        invitation_id: UUID,
        accepted_user_id: str,
        now: datetime,
    ) -> Invitation | None: ...

    def release_processing(self, invitation_id: UUID, now: datetime) -> Invitation | None: ...


class InvitationNotFoundError(Exception):
    """O convite solicitado não existe."""


class InvitationUnavailableError(Exception):
    """O convite existe, mas não pode mais ser utilizado."""


class InvitationConflictError(Exception):
    """A operação administrativa conflita com o estado atual."""


class InvitationTransitionError(Exception):
    """Uma transição interna não pôde ser concluída com segurança."""


@dataclass(frozen=True, slots=True)
class IssuedInvitation:
    """Entrega o token aberto uma única vez junto ao registro persistido."""

    invitation: Invitation
    token: str = field(repr=False)


def utc_now() -> datetime:
    """Fornece um instante UTC consciente de fuso."""

    return datetime.now(UTC)


class InvitationService:
    """Coordena regras, persistência e limites transacionais dos convites."""

    def __init__(
        self,
        session: Session,
        *,
        repository: InvitationRepositoryPort | None = None,
        clock: Clock = utc_now,
        token_factory: TokenFactory = generate_invitation_token,
    ) -> None:
        self._session = session
        self._repository = repository if repository is not None else InvitationRepository(session)
        self._clock = clock
        self._token_factory = token_factory

    def issue(self, *, role: InvitationRole, created_by: str) -> IssuedInvitation:
        """Cria um convite de 24 horas e retorna o segredo somente nesta chamada."""

        if not isinstance(role, InvitationRole):
            raise ValueError("role must be an invitation role")
        if not created_by.strip():
            raise ValueError("created_by must not be empty")

        now = self._now()
        token = self._token_factory()
        invitation = Invitation(
            token_hash=hash_invitation_token(token),
            role=role,
            status=InvitationStatus.pending,
            created_by=created_by,
            created_at=now,
            expires_at=now + INVITATION_LIFETIME,
        )
        try:
            self._repository.add(invitation)
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
        return IssuedInvitation(invitation=invitation, token=token)

    def get(self, invitation_id: UUID) -> Invitation:
        """Obtém um convite administrativo sem revelar seu hash externamente."""

        invitation = self._repository.get(invitation_id)
        if invitation is None:
            self._session.rollback()
            raise InvitationNotFoundError
        return invitation

    def list(self, *, offset: int = 0, limit: int = DEFAULT_LIST_LIMIT) -> Sequence[Invitation]:
        """Lista convites com paginação defensiva."""

        if offset < 0:
            raise ValueError("offset must not be negative")
        if not 1 <= limit <= MAX_LIST_LIMIT:
            raise ValueError(f"limit must be between 1 and {MAX_LIST_LIMIT}")
        return self._repository.list(offset=offset, limit=limit)

    def validate(self, token: str) -> Invitation:
        """Valida o token sem alterar o estado persistido do convite."""

        invitation = self._repository.get_by_token_hash(hash_invitation_token(token))
        if invitation is None:
            self._session.rollback()
            raise InvitationNotFoundError
        if (
            invitation.status is not InvitationStatus.pending
            or invitation.expires_at <= self._now()
        ):
            self._session.rollback()
            raise InvitationUnavailableError
        return invitation

    def revoke(self, invitation_id: UUID) -> Invitation:
        """Revoga um convite pendente; revogado ou expirado é idempotente."""

        now = self._now()
        revoked = self._repository.revoke_pending(invitation_id, now)
        if revoked is not None:
            self._session.commit()
            return revoked

        current = self._repository.get(invitation_id)
        if current is None:
            self._session.rollback()
            raise InvitationNotFoundError
        if current.status in {InvitationStatus.revoked, InvitationStatus.expired}:
            self._session.rollback()
            return current

        self._session.rollback()
        raise InvitationConflictError

    def begin_processing(self, token: str) -> Invitation:
        """Reserva atomicamente um convite válido para uma única tentativa."""

        token_hash = hash_invitation_token(token)
        now = self._now()
        claimed = self._repository.claim_pending(token_hash, now)
        if claimed is not None:
            self._session.commit()
            return claimed

        expired = self._repository.expire_pending(token_hash, now)
        if expired is not None:
            self._session.commit()
            raise InvitationUnavailableError

        current = self._repository.get_by_token_hash(token_hash)
        self._session.rollback()
        if current is None:
            raise InvitationNotFoundError
        raise InvitationUnavailableError

    def complete(self, invitation_id: UUID, *, accepted_user_id: str) -> Invitation:
        """Marca como usado um convite após o provisionamento confirmado."""

        if not accepted_user_id.strip():
            raise ValueError("accepted_user_id must not be empty")

        completed = self._repository.complete_processing(
            invitation_id,
            accepted_user_id,
            self._now(),
        )
        if completed is not None:
            self._session.commit()
            return completed

        current = self._repository.get(invitation_id)
        if (
            current is not None
            and current.status is InvitationStatus.used
            and current.accepted_user_id == accepted_user_id
        ):
            self._session.rollback()
            return current

        self._session.rollback()
        if current is None:
            raise InvitationNotFoundError
        raise InvitationTransitionError

    def release(self, invitation_id: UUID) -> Invitation:
        """Devolve uma reserva falha a pendente ou materializa sua expiração."""

        released = self._repository.release_processing(invitation_id, self._now())
        if released is not None:
            self._session.commit()
            return released

        current = self._repository.get(invitation_id)
        self._session.rollback()
        if current is None:
            raise InvitationNotFoundError
        raise InvitationTransitionError

    def _now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("clock must return a timezone-aware datetime")
        return now.astimezone(UTC)
