from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class OperationTiming:
    """One timed operation (see docs/33-legal-collaboration.md —
    Observabilité)."""

    operation: str
    duration_ms: float
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class WorkspaceActivityMetrics:
    """A point-in-time snapshot of a workspace's collaboration
    activity — the counts called out in the sprint brief: tasks,
    validations, comments, notifications, plus member counts."""

    workspace_id: str
    member_count: int
    active_member_count: int
    task_count: int
    validated_task_count: int
    comment_count: int
    approval_count: int
    pending_approval_count: int
    notification_count: int
    computed_at: datetime
