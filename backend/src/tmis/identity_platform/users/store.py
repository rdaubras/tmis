from tmis.identity_platform.users.schemas import User


class InMemoryUserStore:
    def __init__(self) -> None:
        self._users: dict[str, User] = {}

    def save(self, user: User) -> None:
        self._users[user.id] = user

    def get(self, firm_id: str, user_id: str) -> User | None:
        user = self._users.get(user_id)
        if user is None or user.firm_id != firm_id:
            return None
        return user

    def get_by_email(self, firm_id: str, email: str) -> User | None:
        for user in self._users.values():
            if user.firm_id == firm_id and user.email == email:
                return user
        return None

    def list_for_firm(self, firm_id: str) -> list[User]:
        return [u for u in self._users.values() if u.firm_id == firm_id]
