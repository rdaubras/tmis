from typing import Protocol

from tmis.collaboration.roles.schemas import Role, RoleAssignment


class RoleAssignmentStorePort(Protocol):
    """Port implemented by every interchangeable role-assignment store."""

    def assign(self, workspace_id: str, member_id: str, role: Role) -> RoleAssignment: ...

    def get_role(self, workspace_id: str, member_id: str) -> Role | None: ...

    def list_by_role(self, workspace_id: str, role: Role) -> list[str]: ...
