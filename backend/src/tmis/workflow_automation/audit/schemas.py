import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


def new_workflow_audit_id() -> str:
    return f"wf-audit-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class WorkflowAuditEntry:
    """One append-only entry in the workflow-automation audit trail —
    "toutes les automatisations doivent être auditables" (sprint
    requirement)."""

    id: str
    firm_id: str
    workflow_id: str
    execution_id: str | None
    actor_id: str
    action: str
    detail: str = ""
    metadata: dict[str, str] = field(default_factory=dict)
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
