from datetime import datetime
from typing import Protocol

from tmis.collaboration.tasks.schemas import Task, TaskPriority
from tmis.collaboration.workflow.schemas import WorkflowStatus


class TaskStorePort(Protocol):
    """Port implemented by every interchangeable task store."""

    def get(self, task_id: str) -> Task | None: ...

    def save(self, task: Task) -> None: ...

    def list_for_workspace(self, workspace_id: str) -> list[Task]: ...

    def list_for_case(self, case_id: str) -> list[Task]: ...

    def list_for_assignee(self, assignee_id: str) -> list[Task]: ...


class TaskServicePort(Protocol):
    """Port implemented by every interchangeable task service."""

    def create(
        self,
        workspace_id: str,
        title: str,
        description: str = "",
        *,
        case_id: str | None = None,
        assignee_id: str | None = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_date: datetime | None = None,
        depends_on: set[str] | None = None,
    ) -> Task: ...

    def get(self, task_id: str) -> Task | None: ...

    def assign(self, task_id: str, assignee_id: str) -> Task: ...

    def add_document(self, task_id: str, document_id: str) -> Task: ...

    def link_comment(self, task_id: str, comment_id: str) -> Task: ...

    def can_start(self, task_id: str) -> bool: ...

    def update_status(self, task_id: str, target: WorkflowStatus) -> Task: ...
