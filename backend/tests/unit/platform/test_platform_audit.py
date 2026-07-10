from tmis.collaboration.audit.store import InMemoryAuditStore
from tmis.collaboration.audit.trail import AuditTrail
from tmis.collaboration.permissions.engine import ConfigurablePermissionEngine
from tmis.collaboration.permissions.schemas import Permission
from tmis.collaboration.roles.schemas import Role
from tmis.collaboration.roles.store import InMemoryRoleAssignmentStore
from tmis.collaboration.workspace.schemas import Workspace
from tmis.collaboration.workspace.store import InMemoryWorkspaceStore
from tmis.platform.audit.engine import PermissionAuditEngine, PlatformAuditEngine
from tmis.platform.audit.schemas import detect_anomaly


def test_platform_audit_engine_aggregates_every_workspace_of_a_firm() -> None:
    workspaces = InMemoryWorkspaceStore()
    workspaces.save(Workspace(id="ws-1", firm_id="firm-1", name="Workspace 1"))
    workspaces.save(Workspace(id="ws-2", firm_id="firm-1", name="Workspace 2"))
    workspaces.save(Workspace(id="ws-3", firm_id="firm-2", name="Other firm"))

    audit_store = InMemoryAuditStore()
    trail = AuditTrail(audit_store)
    trail.record("ws-1", "user-1", "case.created", "case", "case-1")
    trail.record("ws-2", "user-1", "document.uploaded", "document", "doc-1")
    trail.record("ws-3", "user-2", "case.created", "case", "case-2")

    engine = PlatformAuditEngine(workspaces, trail)
    entries = engine.list_for_firm("firm-1")

    assert {e.target_id for e in entries} == {"case-1", "doc-1"}


def test_detect_anomaly_flags_a_client_with_overridden_permissions() -> None:
    effective = frozenset({Permission.CASE_READ, Permission.DOCUMENT_READ, Permission.CASE_WRITE})

    reason = detect_anomaly(Role.CLIENT, effective)

    assert reason != ""
    assert "case.write" in reason


def test_detect_anomaly_is_silent_for_a_client_within_its_default_permissions() -> None:
    effective = frozenset({Permission.CASE_READ, Permission.DOCUMENT_READ})

    assert detect_anomaly(Role.CLIENT, effective) == ""


def test_detect_anomaly_never_flags_non_client_roles() -> None:
    assert detect_anomaly(Role.ADMINISTRATOR, frozenset(Permission)) == ""


def test_permission_audit_engine_flags_a_client_granted_an_override() -> None:
    roles = InMemoryRoleAssignmentStore()
    roles.assign("ws-1", "member-1", Role.CLIENT)
    permissions = ConfigurablePermissionEngine()
    permissions.grant_override("ws-1", "member-1", Permission.CASE_WRITE)

    engine = PermissionAuditEngine(roles, permissions)
    entries = engine.audit_workspace("ws-1")

    client_entry = next(e for e in entries if e.member_id == "member-1")
    assert client_entry.anomalous is True


def test_permission_audit_engine_does_not_flag_a_clean_client() -> None:
    roles = InMemoryRoleAssignmentStore()
    roles.assign("ws-1", "member-1", Role.CLIENT)
    permissions = ConfigurablePermissionEngine()

    engine = PermissionAuditEngine(roles, permissions)
    entries = engine.audit_workspace("ws-1")

    client_entry = next(e for e in entries if e.member_id == "member-1")
    assert client_entry.anomalous is False
