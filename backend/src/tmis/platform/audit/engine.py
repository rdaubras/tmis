from tmis.collaboration.audit.ports import AuditTrailPort
from tmis.collaboration.audit.schemas import AuditEntry
from tmis.collaboration.permissions.ports import PermissionEnginePort
from tmis.collaboration.permissions.schemas import Permission
from tmis.collaboration.roles.ports import RoleAssignmentStorePort
from tmis.collaboration.roles.schemas import Role
from tmis.collaboration.workspace.ports import WorkspaceStorePort
from tmis.platform.audit.schemas import PermissionAuditEntry, detect_anomaly


class PlatformAuditEngine:
    """Implements `PlatformAuditPort`: composes
    `tmis.collaboration.workspace.WorkspaceStorePort` (to find every
    workspace a firm owns) and `tmis.collaboration.audit.AuditTrailPort`
    (to read each workspace's audit trail) into one firm-wide,
    chronologically sorted view — no separate storage of its own."""

    def __init__(self, workspace_store: WorkspaceStorePort, audit_trail: AuditTrailPort) -> None:
        self._workspaces = workspace_store
        self._audit_trail = audit_trail

    def list_for_firm(self, firm_id: str) -> list[AuditEntry]:
        entries: list[AuditEntry] = []
        for workspace in self._workspaces.list_for_firm(firm_id):
            entries.extend(self._audit_trail.list_for_workspace(workspace.id))
        return sorted(entries, key=lambda e: e.occurred_at)


class PermissionAuditEngine:
    """Implements `PermissionAuditPort`: resolves every member's
    effective permission set (role matrix + per-member overrides) in a
    workspace and flags the one anomaly rule shipped this sprint (see
    `tmis.platform.audit.schemas.detect_anomaly`)."""

    def __init__(
        self, role_store: RoleAssignmentStorePort, permission_engine: PermissionEnginePort
    ) -> None:
        self._roles = role_store
        self._permissions = permission_engine

    def audit_workspace(self, workspace_id: str) -> list[PermissionAuditEntry]:
        entries: list[PermissionAuditEntry] = []
        for role in Role:
            for member_id in self._roles.list_by_role(workspace_id, role):
                effective = frozenset(
                    p
                    for p in Permission
                    if self._permissions.has_permission(workspace_id, member_id, role, p)
                )
                reason = detect_anomaly(role, effective)
                entries.append(
                    PermissionAuditEntry(
                        workspace_id=workspace_id,
                        member_id=member_id,
                        role=role,
                        effective_permissions=effective,
                        anomalous=bool(reason),
                        reason=reason,
                    )
                )
        return entries
