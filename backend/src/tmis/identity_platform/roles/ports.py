from typing import Protocol

from tmis.identity_platform.roles.schemas import Role, RoleAssignment


class RoleAssignmentStorePort(Protocol):
    def save(self, assignment: RoleAssignment) -> None: ...

    def list_for_user(self, firm_id: str, user_id: str) -> list[Role]: ...

    def remove(self, firm_id: str, user_id: str, role: Role) -> None: ...
