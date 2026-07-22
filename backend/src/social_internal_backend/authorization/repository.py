"""Persistência dos papéis corporativos."""

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from social_internal_backend.models import UserRole, UserRoleAssignment


class UserRoleAssignmentRepository:
    """Acessa papéis no banco próprio e nunca no banco do Synapse."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def lock_for_bootstrap(self) -> None:
        """Serializa o procedimento único de bootstrap no PostgreSQL."""

        self._session.execute(text("LOCK TABLE user_role_assignments IN EXCLUSIVE MODE"))

    def add(self, assignment: UserRoleAssignment) -> UserRoleAssignment:
        """Adiciona e materializa uma atribuição na transação atual."""

        self._session.add(assignment)
        self._session.flush()
        return assignment

    def get(self, matrix_user_id: str) -> UserRoleAssignment | None:
        """Obtém o papel associado à identidade Matrix exata."""

        return self._session.get(UserRoleAssignment, matrix_user_id)

    def get_first_platform_admin(self) -> UserRoleAssignment | None:
        """Localiza um administrador que prove que o bootstrap já ocorreu."""

        statement = (
            select(UserRoleAssignment)
            .where(UserRoleAssignment.role == UserRole.platform_admin)
            .order_by(UserRoleAssignment.granted_at, UserRoleAssignment.matrix_user_id)
            .limit(1)
        )
        return self._session.scalars(statement).one_or_none()
