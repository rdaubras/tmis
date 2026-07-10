import uuid
from datetime import UTC, datetime

from tmis.collaboration.tasks.ports import TaskStorePort
from tmis.collaboration.tasks.schemas import Task, TaskPriority
from tmis.collaboration.tasks.store import InMemoryTaskStore
from tmis.collaboration.workflow.engine import ConfigurableWorkflowEngine
from tmis.collaboration.workflow.ports import WorkflowEnginePort
from tmis.collaboration.workflow.schemas import WorkflowStatus

_DONE_STATUSES = {WorkflowStatus.VALIDATED, WorkflowStatus.ARCHIVED}


class TaskService:
    """Creates and mutates `Task`s, delegating every status change to a
    `WorkflowEnginePort` so the same transition rules apply everywhere
    in TMIS (see docs/33-legal-collaboration.md — Task Engine)."""

    def __init__(
        self,
        store: TaskStorePort | None = None,
        workflow_engine: WorkflowEnginePort | None = None,
    ) -> None:
        self._store: TaskStorePort = store or InMemoryTaskStore()
        self._workflow_engine: WorkflowEnginePort = workflow_engine or ConfigurableWorkflowEngine()

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
    ) -> Task:
        now = datetime.now(UTC)
        task = Task(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            title=title,
            description=description,
            case_id=case_id,
            assignee_id=assignee_id,
            priority=priority,
            due_date=due_date,
            depends_on=set(depends_on or set()),
            created_at=now,
            updated_at=now,
        )
        self._store.save(task)
        return task

    def get(self, task_id: str) -> Task | None:
        return self._store.get(task_id)

    def assign(self, task_id: str, assignee_id: str) -> Task:
        task = self._require_task(task_id)
        task.assignee_id = assignee_id
        task.updated_at = datetime.now(UTC)
        self._store.save(task)
        return task

    def add_document(self, task_id: str, document_id: str) -> Task:
        task = self._require_task(task_id)
        task.document_ids.add(document_id)
        self._store.save(task)
        return task

    def link_comment(self, task_id: str, comment_id: str) -> Task:
        task = self._require_task(task_id)
        task.comment_ids.add(comment_id)
        self._store.save(task)
        return task

    def can_start(self, task_id: str) -> bool:
        """A task with unmet dependencies can still exist, but this
        tells the caller whether every task it `depends_on` is done —
        purely advisory, `update_status` does not enforce it, so a
        workspace can override the rule for urgent work."""
        task = self._require_task(task_id)
        for dependency_id in task.depends_on:
            dependency = self._store.get(dependency_id)
            if dependency is None or dependency.status not in _DONE_STATUSES:
                return False
        return True

    def update_status(self, task_id: str, target: WorkflowStatus) -> Task:
        task = self._require_task(task_id)
        task.status = self._workflow_engine.transition(task.status, target)
        task.updated_at = datetime.now(UTC)
        self._store.save(task)
        return task

    def _require_task(self, task_id: str) -> Task:
        task = self._store.get(task_id)
        if task is None:
            raise ValueError(f"Unknown task {task_id!r}")
        return task
