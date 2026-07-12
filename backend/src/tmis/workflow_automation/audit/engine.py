import csv
import io

from tmis.workflow_automation.audit.ports import WorkflowAuditStorePort
from tmis.workflow_automation.audit.schemas import WorkflowAuditEntry, new_workflow_audit_id

_CSV_FIELDS = (
    "id",
    "workflow_id",
    "execution_id",
    "actor_id",
    "action",
    "detail",
    "recorded_at",
)


class WorkflowAuditEngine:
    """A specialized, append-only journal of every workflow-automation
    event worth auditing (created, versioned, activated, executed,
    rolled back, cancelled...). Mirrors
    `ai_governance.audit.AIAuditEngine`."""

    def __init__(self, store: WorkflowAuditStorePort) -> None:
        self._store = store

    def record(
        self,
        firm_id: str,
        workflow_id: str,
        actor_id: str,
        action: str,
        *,
        execution_id: str | None = None,
        detail: str = "",
        metadata: dict[str, str] | None = None,
    ) -> WorkflowAuditEntry:
        entry = WorkflowAuditEntry(
            id=new_workflow_audit_id(),
            firm_id=firm_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
            actor_id=actor_id,
            action=action,
            detail=detail,
            metadata=metadata or {},
        )
        self._store.add(entry)
        return entry

    def list_for_firm(self, firm_id: str) -> list[WorkflowAuditEntry]:
        return self._store.list_for_firm(firm_id)

    def list_for_workflow(self, firm_id: str, workflow_id: str) -> list[WorkflowAuditEntry]:
        return self._store.list_for_workflow(firm_id, workflow_id)

    def export_csv(self, firm_id: str) -> str:
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=_CSV_FIELDS)
        writer.writeheader()
        for entry in self.list_for_firm(firm_id):
            writer.writerow(
                {
                    "id": entry.id,
                    "workflow_id": entry.workflow_id,
                    "execution_id": entry.execution_id or "",
                    "actor_id": entry.actor_id,
                    "action": entry.action,
                    "detail": entry.detail,
                    "recorded_at": entry.recorded_at.isoformat(),
                }
            )
        return buffer.getvalue()
