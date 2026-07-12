from tmis.identity_platform.roles.ports import RoleAssignmentStorePort
from tmis.identity_platform.roles.schemas import Role, RoleAssignment


class RoleEngine:
    def __init__(self, store: RoleAssignmentStorePort) -> None:
        self._store = store

    def assign(self, firm_id: str, user_id: str, role: Role) -> RoleAssignment:
        assignment = RoleAssignment(firm_id=firm_id, user_id=user_id, role=role)
        self._store.save(assignment)
        return assignment

    def revoke(self, firm_id: str, user_id: str, role: Role) -> None:
        self._store.remove(firm_id, user_id, role)

    def roles_for_user(self, firm_id: str, user_id: str) -> list[Role]:
        return self._store.list_for_user(firm_id, user_id)
