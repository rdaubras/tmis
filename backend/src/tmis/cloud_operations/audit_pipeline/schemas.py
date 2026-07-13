from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class AuditSource(StrEnum):
    """The three firm-scoped audit trails this pipeline unifies —
    all three already expose a uniform `.list_for_firm(firm_id)`,
    unlike `collaboration.audit`/`platform.audit` (workspace-scoped,
    no direct `firm_id` field), which stay out of scope for this
    pipeline until a workspace→firm adapter is built."""

    SECURITY = "security"
    AI_GOVERNANCE = "ai_governance"
    WORKFLOW = "workflow"


@dataclass(frozen=True, slots=True)
class AuditPipelineEvent:
    """One normalized cross-module audit event — the common shape
    `identity_platform.audit.SecurityAuditEntry`,
    `ai_governance.audit.AIAuditEntry`, and
    `workflow_automation.audit.WorkflowAuditEntry` are each mapped
    into, so a single timeline can merge all three without the caller
    needing to know each source's native schema."""

    firm_id: str
    source: AuditSource
    action: str
    summary: str
    occurred_at: datetime
