from tmis.identity_platform.roles.schemas import Role, RoleAssignment


class InMemoryRoleAssignmentStore:
    def __init__(self) -> None:
        self._assignments: set[tuple[str, str, Role]] = set()

    def save(self, assignment: RoleAssignment) -> None:
        self._assignments.add((assignment.firm_id, assignment.user_id, assignment.role))

    def list_for_user(self, firm_id: str, user_id: str) -> list[Role]:
        return [r for f, u, r in self._assignments if f == firm_id and u == user_id]

    def remove(self, firm_id: str, user_id: str, role: Role) -> None:
        self._assignments.discard((firm_id, user_id, role))
