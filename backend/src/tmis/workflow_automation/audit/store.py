from tmis.workflow_automation.audit.schemas import WorkflowAuditEntry


class InMemoryWorkflowAuditStore:
    def __init__(self) -> None:
        self._entries: list[WorkflowAuditEntry] = []

    def add(self, entry: WorkflowAuditEntry) -> None:
        self._entries.append(entry)

    def list_for_firm(self, firm_id: str) -> list[WorkflowAuditEntry]:
        return [e for e in self._entries if e.firm_id == firm_id]

    def list_for_workflow(self, firm_id: str, workflow_id: str) -> list[WorkflowAuditEntry]:
        return [
            e for e in self._entries if e.firm_id == firm_id and e.workflow_id == workflow_id
        ]
