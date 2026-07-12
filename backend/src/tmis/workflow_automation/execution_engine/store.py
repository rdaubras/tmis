from tmis.workflow_automation.execution_engine.schemas import WorkflowExecution


class InMemoryExecutionStore:
    def __init__(self) -> None:
        self._executions: dict[tuple[str, str], WorkflowExecution] = {}

    def add(self, execution: WorkflowExecution) -> None:
        self._executions[(execution.firm_id, execution.id)] = execution

    def get(self, firm_id: str, execution_id: str) -> WorkflowExecution | None:
        return self._executions.get((firm_id, execution_id))

    def list_for_workflow(self, firm_id: str, workflow_id: str) -> list[WorkflowExecution]:
        return [
            e
            for (fid, _), e in self._executions.items()
            if fid == firm_id and e.workflow_id == workflow_id
        ]
