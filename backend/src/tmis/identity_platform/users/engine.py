from tmis.identity_platform.users.ports import UserStorePort
from tmis.identity_platform.users.schemas import User, UserStatus, new_user_id


class UserEngine:
    def __init__(self, store: UserStorePort) -> None:
        self._store = store

    def create(
        self,
        firm_id: str,
        email: str,
        display_name: str,
        team_id: str | None = None,
        department_id: str | None = None,
    ) -> User:
        user = User(
            id=new_user_id(),
            firm_id=firm_id,
            email=email,
            display_name=display_name,
            team_id=team_id,
            department_id=department_id,
        )
        self._store.save(user)
        return user

    def get(self, firm_id: str, user_id: str) -> User:
        user = self._store.get(firm_id, user_id)
        if user is None:
            raise KeyError(user_id)
        return user

    def set_status(self, firm_id: str, user_id: str, status: UserStatus) -> User:
        user = self.get(firm_id, user_id)
        user.status = status
        self._store.save(user)
        return user

    def list_for_firm(self, firm_id: str) -> list[User]:
        return self._store.list_for_firm(firm_id)
