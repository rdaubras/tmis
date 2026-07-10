from dataclasses import dataclass

from tmis.collaboration.permissions.schemas import Permission
from tmis.collaboration.roles.schemas import Role

_CLIENT_ALLOWED_PERMISSIONS = frozenset({Permission.CASE_READ, Permission.DOCUMENT_READ})


@dataclass(frozen=True, slots=True)
class PermissionAuditEntry:
    """One member's resolved (role matrix + overrides) permission set
    in a workspace (see docs/47-guide-securite-entreprise.md —
    Contrôle d'accès systématique), plus whether it looks anomalous."""

    workspace_id: str
    member_id: str
    role: Role
    effective_permissions: frozenset[Permission]
    anomalous: bool
    reason: str = ""


def detect_anomaly(role: Role, effective_permissions: frozenset[Permission]) -> str:
    """The one anomaly rule shipped this sprint: a `CLIENT` — the
    read-only role by design (see docs/34-guide-roles.md) — should
    never end up with anything beyond case/document read, which can
    only happen through a `grant_override`. Returns a human-readable
    reason, or `""` if nothing looks wrong."""
    if role is Role.CLIENT:
        extra = effective_permissions - _CLIENT_ALLOWED_PERMISSIONS
        if extra:
            extra_names = sorted(p.value for p in extra)
            return f"CLIENT role has extra permissions via override: {extra_names}"
    return ""
