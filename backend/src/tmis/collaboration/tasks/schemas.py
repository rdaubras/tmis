from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from tmis.collaboration.workflow.schemas import WorkflowStatus


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass(slots=True)
class Task:
    """A unit of work in a workspace (see
    docs/33-legal-collaboration.md — Task Engine). `depends_on` lists
    other task ids that must be done first — purely descriptive at this
    stage, enforced by `TaskService` only when transitioning out of
    `TODO` (see `TaskService.can_start`)."""

    id: str
    workspace_id: str
    title: str
    description: str
    case_id: str | None = None
    assignee_id: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: datetime | None = None
    status: WorkflowStatus = WorkflowStatus.TODO
    document_ids: set[str] = field(default_factory=set)
    comment_ids: set[str] = field(default_factory=set)
    depends_on: set[str] = field(default_factory=set)
    created_at: datetime | None = None
    updated_at: datetime | None = None
