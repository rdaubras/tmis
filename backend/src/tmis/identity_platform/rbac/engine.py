from tmis.identity_platform.permissions.schemas import Permission
from tmis.identity_platform.rbac.schemas import DEFAULT_ROLE_PERMISSIONS
from tmis.identity_platform.roles.schemas import Role


class RbacEngine:
    """Role-Based Access Control: a configurable role → permission
    matrix. `grant`/`revoke` mutate the matrix without touching any
    caller — the same registry-without-modifying-the-engine
    extensibility already used by `authentication.AuthenticationEngine`
    (Sprint 18) and `workflow_automation.trigger_engine`."""

    def __init__(self, matrix: dict[Role, frozenset[Permission]] | None = None) -> None:
        self._matrix: dict[Role, frozenset[Permission]] = (
            dict(matrix) if matrix is not None else dict(DEFAULT_ROLE_PERMISSIONS)
        )

    def grant(self, role: Role, permission: Permission) -> None:
        self._matrix[role] = self._matrix.get(role, frozenset()) | {permission}

    def revoke(self, role: Role, permission: Permission) -> None:
        self._matrix[role] = self._matrix.get(role, frozenset()) - {permission}

    def has_permission(self, roles: tuple[Role, ...], permission: Permission) -> bool:
        return any(permission in self._matrix.get(role, frozenset()) for role in roles)

    def permissions_for(self, role: Role) -> frozenset[Permission]:
        return self._matrix.get(role, frozenset())
