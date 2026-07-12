from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    """Firm-wide enterprise roles — distinct scope from
    `collaboration.roles.Role` (workspace-membership roles, Sprint 8).
    Same architectural role name ("a role"), two disjoint scopes: this
    one governs firm-wide authorization (RBAC/ABAC/policies), that one
    governs who can do what on a single workspace's Kanban board.
    Documented, not merged — same convention already applied to the
    `GovernanceEngine`/`PolicyEngine` collisions."""

    PARTNER = "partner"
    ASSOCIATE = "associate"
    COUNSEL = "counsel"
    PARALEGAL = "paralegal"
    ASSISTANT = "assistant"
    IT_ADMIN = "it_admin"


@dataclass(frozen=True, slots=True)
class RoleAssignment:
    firm_id: str
    user_id: str
    role: Role
