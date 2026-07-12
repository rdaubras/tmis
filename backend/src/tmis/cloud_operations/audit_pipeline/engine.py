from tmis.ai_governance.audit.engine import AIAuditEngine
from tmis.cloud_operations.audit_pipeline.schemas import AuditPipelineEvent, AuditSource
from tmis.identity_platform.audit.engine import SecurityAuditEngine
from tmis.workflow_automation.audit.engine import WorkflowAuditEngine


class AuditPipelineEngine:
    """Merges the three firm-scoped audit trails already built
    (`identity_platform.audit`, Sprint 19; `ai_governance.audit`,
    Sprint 15; `workflow_automation.audit`, Sprint 17) into one
    correlated timeline, rather than a fourth audit store — "chaque
    action peut être auditée et corrélée" (sprint requirement) without
    reimplementing what each of those three already records."""

    def __init__(
        self,
        security_audit: SecurityAuditEngine,
        ai_audit: AIAuditEngine,
        workflow_audit: WorkflowAuditEngine,
    ) -> None:
        self._security_audit = security_audit
        self._ai_audit = ai_audit
        self._workflow_audit = workflow_audit

    def timeline(self, firm_id: str) -> list[AuditPipelineEvent]:
        events: list[AuditPipelineEvent] = []
        events.extend(
            AuditPipelineEvent(
                firm_id=entry.firm_id,
                source=AuditSource.SECURITY,
                action=entry.event_type,
                summary=entry.summary,
                occurred_at=entry.occurred_at,
            )
            for entry in self._security_audit.list_for_firm(firm_id)
        )
        events.extend(
            AuditPipelineEvent(
                firm_id=entry.firm_id,
                source=AuditSource.AI_GOVERNANCE,
                action=entry.action,
                summary=entry.prompt or entry.action,
                occurred_at=entry.recorded_at,
            )
            for entry in self._ai_audit.list_for_firm(firm_id)
        )
        events.extend(
            AuditPipelineEvent(
                firm_id=entry.firm_id,
                source=AuditSource.WORKFLOW,
                action=entry.action,
                summary=entry.detail or entry.action,
                occurred_at=entry.recorded_at,
            )
            for entry in self._workflow_audit.list_for_firm(firm_id)
        )
        events.sort(key=lambda e: e.occurred_at)
        return events
