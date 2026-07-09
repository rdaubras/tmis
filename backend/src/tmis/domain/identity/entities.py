import uuid
from dataclasses import dataclass, field

from tmis.domain.identity.value_objects import DEFAULT_ROLE_PERMISSIONS, Email, Permission, Role


@dataclass
class User:
    """Aggregate root of the `identity` bounded context."""

    id: uuid.UUID
    firm_id: uuid.UUID
    email: Email
    full_name: str
    role: Role
    hashed_password: str
    mfa_enabled: bool = False
    is_active: bool = True
    extra_permissions: frozenset[Permission] = field(default_factory=frozenset)

    @property
    def permissions(self) -> frozenset[Permission]:
        return DEFAULT_ROLE_PERMISSIONS[self.role] | self.extra_permissions

    def has_permission(self, permission: Permission) -> bool:
        return self.is_active and permission in self.permissions
