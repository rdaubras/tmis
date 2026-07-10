from tmis.collaboration.permissions.schemas import Permission
from tmis.collaboration.roles.schemas import Role

_DEFAULT_MATRIX: dict[Role, set[Permission]] = {
    Role.ADMINISTRATOR: set(Permission),
    Role.ASSOCIATE: set(Permission) - {Permission.WORKSPACE_MANAGE},
    Role.COLLABORATOR: {
        Permission.CASE_READ,
        Permission.CASE_WRITE,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_WRITE,
        Permission.TASK_CREATE,
        Permission.TASK_ASSIGN,
        Permission.TASK_UPDATE,
        Permission.COMMENT_WRITE,
        Permission.APPROVAL_REQUEST,
        Permission.SHARING_CREATE_LINK,
    },
    Role.JURIST: {
        Permission.CASE_READ,
        Permission.CASE_WRITE,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_WRITE,
        Permission.TASK_CREATE,
        Permission.TASK_UPDATE,
        Permission.COMMENT_WRITE,
        Permission.APPROVAL_REQUEST,
    },
    Role.ASSISTANT: {
        Permission.CASE_READ,
        Permission.DOCUMENT_READ,
        Permission.TASK_UPDATE,
        Permission.COMMENT_WRITE,
    },
    Role.CLIENT: {
        Permission.CASE_READ,
        Permission.DOCUMENT_READ,
    },
}


class ConfigurablePermissionEngine:
    """Implements `PermissionEnginePort`: a default role -> permissions
    matrix, fully reconfigurable (`set_role_permissions`), plus
    per-member grant/revoke overrides on top of whatever the role
    already allows or denies (see docs/35-guide-permissions.md).

    Precedence: an explicit per-member revoke always wins over both the
    role matrix and a grant (deny-overrides), so a workspace admin can
    always lock down one member's access without touching the role
    definition shared by everyone else.
    """

    def __init__(self, matrix: dict[Role, set[Permission]] | None = None) -> None:
        self._matrix: dict[Role, set[Permission]] = {
            role: set(permissions) for role, permissions in (matrix or _DEFAULT_MATRIX).items()
        }
        self._grants: dict[tuple[str, str], set[Permission]] = {}
        self._revokes: dict[tuple[str, str], set[Permission]] = {}

    def has_permission(
        self, workspace_id: str, member_id: str, role: Role, permission: Permission
    ) -> bool:
        key = (workspace_id, member_id)
        if permission in self._revokes.get(key, set()):
            return False
        if permission in self._grants.get(key, set()):
            return True
        return permission in self._matrix.get(role, set())

    def grant_override(self, workspace_id: str, member_id: str, permission: Permission) -> None:
        key = (workspace_id, member_id)
        self._grants.setdefault(key, set()).add(permission)
        self._revokes.get(key, set()).discard(permission)

    def revoke_override(self, workspace_id: str, member_id: str, permission: Permission) -> None:
        key = (workspace_id, member_id)
        self._revokes.setdefault(key, set()).add(permission)
        self._grants.get(key, set()).discard(permission)

    def set_role_permissions(self, role: Role, permissions: set[Permission]) -> None:
        self._matrix[role] = set(permissions)
