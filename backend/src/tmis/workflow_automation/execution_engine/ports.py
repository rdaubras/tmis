from typing import Protocol

from tmis.workflow_automation.execution_engine.schemas import WorkflowExecution


class ExecutionStorePort(Protocol):
    def add(self, execution: WorkflowExecution) -> None: ...

    def get(self, firm_id: str, execution_id: str) -> WorkflowExecution | None: ...

    def list_for_workflow(self, firm_id: str, workflow_id: str) -> list[WorkflowExecution]: ...
