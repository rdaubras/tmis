from tmis.workflow_automation.workflow_engine.schemas import Workflow


class InMemoryWorkflowStore:
    def __init__(self) -> None:
        self._workflows: dict[tuple[str, str], Workflow] = {}

    def add(self, workflow: Workflow) -> None:
        self._workflows[(workflow.firm_id, workflow.id)] = workflow

    def get(self, firm_id: str, workflow_id: str) -> Workflow | None:
        return self._workflows.get((firm_id, workflow_id))

    def list_versions(self, firm_id: str, workflow_key: str) -> list[Workflow]:
        versions = [
            w
            for (fid, _), w in self._workflows.items()
            if fid == firm_id and w.workflow_key == workflow_key
        ]
        return sorted(versions, key=lambda w: w.version)

    def list_for_firm(self, firm_id: str) -> list[Workflow]:
        return [w for (fid, _), w in self._workflows.items() if fid == firm_id]
