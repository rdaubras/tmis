from typing import Protocol

from tmis.collaboration.audit.schemas import AuditEntry
from tmis.platform.audit.schemas import PermissionAuditEntry


class PlatformAuditPort(Protocol):
    """Port implemented by every interchangeable platform-wide audit
    reader — an admin-facing view across every workspace of a firm,
    composed from `tmis.collaboration.audit.AuditTrail` (Sprint 8)
    rather than a separate audit log (see
    docs/47-guide-securite-entreprise.md)."""

    def list_for_firm(self, firm_id: str) -> list[AuditEntry]: ...


class PermissionAuditPort(Protocol):
    """Port implemented by every interchangeable permission auditor."""

    def audit_workspace(self, workspace_id: str) -> list[PermissionAuditEntry]: ...
