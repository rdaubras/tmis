from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class QueueItemStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


@dataclass(slots=True)
class QueueItem:
    """One queued synchronization job run — mirrors
    `ai_team.work_queue.WorkItem`'s lifecycle shape but reimplemented
    locally since the LIH is a distinct bounded context. Higher
    `priority` runs first."""

    id: str
    firm_id: str
    job_id: str
    priority: int = 0
    status: QueueItemStatus = QueueItemStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    timeout_seconds: float = 60.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    detail: str | None = None
    error: str | None = None
