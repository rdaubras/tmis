from typing import Protocol

from tmis.collaboration.workflow.schemas import WorkflowStatus


class WorkflowEnginePort(Protocol):
    """Port implemented by every interchangeable workflow engine."""

    def can_transition(self, current: WorkflowStatus, target: WorkflowStatus) -> bool: ...

    def transition(self, current: WorkflowStatus, target: WorkflowStatus) -> WorkflowStatus: ...
