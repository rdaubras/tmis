from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AuditEntry:
    """One historised action (see docs/33-legal-collaboration.md — Audit
    Engine): who did what, when, from where (if available), and the
    before/after state. Append-only — never updated or removed."""

    id: str
    workspace_id: str
    actor_id: str
    action: str
    target_type: str
    target_id: str
    ip_address: str | None
    old_state: dict[str, str] | None
    new_state: dict[str, str] | None
    occurred_at: datetime
    metadata: dict[str, str] = field(default_factory=dict)
