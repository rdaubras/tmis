from typing import Protocol

from tmis.collaboration.permissions.schemas import Permission
from tmis.collaboration.roles.schemas import Role


class PermissionEnginePort(Protocol):
    """Port implemented by every interchangeable permission engine."""

    def has_permission(
        self, workspace_id: str, member_id: str, role: Role, permission: Permission
    ) -> bool: ...

    def grant_override(
        self, workspace_id: str, member_id: str, permission: Permission
    ) -> None: ...

    def revoke_override(
        self, workspace_id: str, member_id: str, permission: Permission
    ) -> None: ...

    def set_role_permissions(self, role: Role, permissions: set[Permission]) -> None: ...
