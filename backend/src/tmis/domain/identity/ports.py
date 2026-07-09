import uuid
from typing import Protocol

from tmis.domain.identity.entities import User
from tmis.domain.identity.value_objects import Email


class UserRepositoryPort(Protocol):
    """Persistence port for the `identity` bounded context."""

    def get_by_id(self, user_id: uuid.UUID, firm_id: uuid.UUID) -> User | None: ...

    def get_by_email(self, email: Email, firm_id: uuid.UUID) -> User | None: ...

    def add(self, user: User) -> None: ...
