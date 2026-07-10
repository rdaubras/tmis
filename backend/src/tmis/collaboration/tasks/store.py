from tmis.collaboration.tasks.schemas import Task


class InMemoryTaskStore:
    """Implements `TaskStorePort` with an in-memory dict."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def get(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def save(self, task: Task) -> None:
        self._tasks[task.id] = task

    def list_for_workspace(self, workspace_id: str) -> list[Task]:
        return [t for t in self._tasks.values() if t.workspace_id == workspace_id]

    def list_for_case(self, case_id: str) -> list[Task]:
        return [t for t in self._tasks.values() if t.case_id == case_id]

    def list_for_assignee(self, assignee_id: str) -> list[Task]:
        return [t for t in self._tasks.values() if t.assignee_id == assignee_id]
