from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

from tmis.ai.schemas.agent import AgentOutput


class WorkItemStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


@dataclass(slots=True)
class WorkItem:
    """One unit of delegated work — a `SubTask` assigned to an agent,
    tracked through its lifecycle (see docs/55-guide-coordinateur.md
    — Work Queue). Higher `priority` runs first."""

    id: str
    sub_task_id: str
    agent_id: str
    priority: int = 0
    status: WorkItemStatus = WorkItemStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    timeout_seconds: float = 60.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: AgentOutput | None = None
    error: str | None = None
