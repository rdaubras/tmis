from tmis.workflow_automation.condition_engine.schemas import Condition
from tmis.workflow_automation.trigger_engine.schemas import Trigger
from tmis.workflow_automation.workflow_engine.ports import WorkflowStorePort
from tmis.workflow_automation.workflow_engine.schemas import (
    Workflow,
    WorkflowStatus,
    WorkflowStep,
    new_workflow_id,
    new_workflow_key,
)


class WorkflowEngine:
    """Creates, versions, activates and archives `Workflow` snapshots.
    Only one version per `workflow_key` may be `ACTIVE` at a time —
    activating a new version automatically archives whichever version
    was previously active, so `trigger_engine`/`execution_engine`
    never have to disambiguate between two active versions of the same
    workflow."""

    def __init__(self, store: WorkflowStorePort) -> None:
        self._store = store

    def create(
        self,
        firm_id: str,
        name: str,
        owner: str,
        *,
        description: str = "",
        triggers: tuple[Trigger, ...] = (),
        conditions: tuple[Condition, ...] = (),
        steps: tuple[WorkflowStep, ...] = (),
    ) -> Workflow:
        workflow = Workflow(
            id=new_workflow_id(),
            workflow_key=new_workflow_key(),
            firm_id=firm_id,
            name=name,
            version=1,
            owner=owner,
            description=description,
            triggers=triggers,
            conditions=conditions,
            steps=steps,
        )
        self._store.add(workflow)
        return workflow

    def new_version(
        self,
        firm_id: str,
        workflow_key: str,
        owner: str,
        *,
        description: str | None = None,
        triggers: tuple[Trigger, ...] | None = None,
        conditions: tuple[Condition, ...] | None = None,
        steps: tuple[WorkflowStep, ...] | None = None,
    ) -> Workflow:
        versions = self._store.list_versions(firm_id, workflow_key)
        if not versions:
            raise KeyError(workflow_key)
        latest = versions[-1]
        new_workflow = Workflow(
            id=new_workflow_id(),
            workflow_key=workflow_key,
            firm_id=firm_id,
            name=latest.name,
            version=latest.version + 1,
            owner=owner,
            description=description if description is not None else latest.description,
            triggers=triggers if triggers is not None else latest.triggers,
            conditions=conditions if conditions is not None else latest.conditions,
            steps=steps if steps is not None else latest.steps,
        )
        self._store.add(new_workflow)
        return new_workflow

    def get(self, firm_id: str, workflow_id: str) -> Workflow:
        workflow = self._store.get(firm_id, workflow_id)
        if workflow is None:
            raise KeyError(workflow_id)
        return workflow

    def list_versions(self, firm_id: str, workflow_key: str) -> list[Workflow]:
        return self._store.list_versions(firm_id, workflow_key)

    def get_active(self, firm_id: str, workflow_key: str) -> Workflow | None:
        for version in self._store.list_versions(firm_id, workflow_key):
            if version.status is WorkflowStatus.ACTIVE:
                return version
        return None

    def activate(self, firm_id: str, workflow_id: str) -> Workflow:
        workflow = self.get(firm_id, workflow_id)
        previous_active = self.get_active(firm_id, workflow.workflow_key)
        if previous_active is not None and previous_active.id != workflow.id:
            previous_active.status = WorkflowStatus.ARCHIVED
        workflow.status = WorkflowStatus.ACTIVE
        return workflow

    def archive(self, firm_id: str, workflow_id: str) -> Workflow:
        workflow = self.get(firm_id, workflow_id)
        workflow.status = WorkflowStatus.ARCHIVED
        return workflow
