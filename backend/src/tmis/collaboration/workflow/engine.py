from tmis.collaboration.workflow.schemas import WorkflowStatus

_DEFAULT_TRANSITIONS: dict[WorkflowStatus, set[WorkflowStatus]] = {
    WorkflowStatus.TODO: {WorkflowStatus.IN_PROGRESS, WorkflowStatus.ARCHIVED},
    WorkflowStatus.IN_PROGRESS: {
        WorkflowStatus.IN_REVIEW, WorkflowStatus.TODO, WorkflowStatus.ARCHIVED,
    },
    WorkflowStatus.IN_REVIEW: {
        WorkflowStatus.TO_VALIDATE, WorkflowStatus.IN_PROGRESS, WorkflowStatus.ARCHIVED,
    },
    WorkflowStatus.TO_VALIDATE: {
        WorkflowStatus.VALIDATED, WorkflowStatus.IN_REVIEW, WorkflowStatus.ARCHIVED,
    },
    WorkflowStatus.VALIDATED: {WorkflowStatus.ARCHIVED},
    WorkflowStatus.ARCHIVED: set(),
}


class ConfigurableWorkflowEngine:
    """Implements `WorkflowEnginePort`: a default linear
    todo -> in_progress -> in_review -> to_validate -> validated
    progression (with a step back allowed at every stage, and archiving
    from anywhere except a terminal archive), fully replaceable via the
    constructor — see docs/36-guide-workflows.md."""

    def __init__(
        self,
        transitions: dict[WorkflowStatus, set[WorkflowStatus]] | None = None,
    ) -> None:
        self._transitions: dict[WorkflowStatus, set[WorkflowStatus]] = {
            status: set(targets)
            for status, targets in (transitions or _DEFAULT_TRANSITIONS).items()
        }

    def can_transition(self, current: WorkflowStatus, target: WorkflowStatus) -> bool:
        return target in self._transitions.get(current, set())

    def transition(self, current: WorkflowStatus, target: WorkflowStatus) -> WorkflowStatus:
        if not self.can_transition(current, target):
            raise ValueError(f"Cannot transition from {current} to {target}")
        return target
