from typing import Protocol

from tmis.workflow_automation.audit.schemas import WorkflowAuditEntry


class WorkflowAuditStorePort(Protocol):
    def add(self, entry: WorkflowAuditEntry) -> None: ...

    def list_for_firm(self, firm_id: str) -> list[WorkflowAuditEntry]: ...

    def list_for_workflow(self, firm_id: str, workflow_id: str) -> list[WorkflowAuditEntry]: ...
