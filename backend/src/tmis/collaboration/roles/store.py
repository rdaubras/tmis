from tmis.collaboration.roles.schemas import Role, RoleAssignment


class InMemoryRoleAssignmentStore:
    """Implements `RoleAssignmentStorePort`. A member holds exactly one
    role per workspace at a time — assigning a new one replaces the
    previous assignment (roles are not additive; permissions overrides
    are, see `permissions/`)."""

    def __init__(self) -> None:
        self._assignments: dict[tuple[str, str], RoleAssignment] = {}

    def assign(self, workspace_id: str, member_id: str, role: Role) -> RoleAssignment:
        assignment = RoleAssignment(workspace_id=workspace_id, member_id=member_id, role=role)
        self._assignments[(workspace_id, member_id)] = assignment
        return assignment

    def get_role(self, workspace_id: str, member_id: str) -> Role | None:
        assignment = self._assignments.get((workspace_id, member_id))
        return assignment.role if assignment else None

    def list_by_role(self, workspace_id: str, role: Role) -> list[str]:
        return [
            member_id
            for (ws_id, member_id), assignment in self._assignments.items()
            if ws_id == workspace_id and assignment.role == role
        ]
