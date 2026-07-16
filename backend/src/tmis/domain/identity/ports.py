import uuid
from typing import Protocol

from tmis.domain.identity.entities import User
from tmis.domain.identity.value_objects import Email


class UserRepositoryPort(Protocol):
    """Persistence port for the `identity` bounded context."""

    def get_by_id(self, user_id: uuid.UUID, firm_id: uuid.UUID) -> User | None: ...

    def get_by_email(self, email: Email) -> User | None:
        """Looks up a user by email alone, with no `firm_id` filter.

        Email is globally unique across firms (see `UserModel.email`,
        `unique=True`) — the login flow only has an email/password pair
        to work with, not a client-supplied tenant, so `firm_id` isn't
        an input here; it comes back as part of the resolved `User`.
        """
        ...

    def add(self, user: User) -> None: ...
