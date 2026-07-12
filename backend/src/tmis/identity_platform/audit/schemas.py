from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class SecurityAuditEntry:
    """One append-only entry derived from a `security_events.
    SecurityEvent` — distinct from `platform.audit`
    (permission-matrix anomalies) and `collaboration.audit`
    (workspace activity): this is the identity/security-specific
    trail — logins, MFA failures, role changes, delegations, new
    devices, session revocations."""

    firm_id: str
    event_type: str
    summary: str
    occurred_at: datetime
