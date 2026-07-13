import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class AsyncJobStatus(StrEnum):
    SCHEDULED = "scheduled"
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    RETRYING = "retrying"
    FAILED = "failed"
    DEAD_LETTERED = "dead_lettered"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


def new_async_job_id() -> str:
    return f"job-{uuid.uuid4().hex[:12]}"


@dataclass(slots=True)
class AsyncJob:
    """One unit of background work. Generalizes the priority/retry/
    timeout shape already duplicated across
    `ai_team.work_queue.WorkItem` and `integration_hub.queue`'s
    equivalent (confirmed structurally identical by the Sprint 23
    Phase 1 audit) and adds the two capabilities neither of those —
    nor any other queue in TMIS — provides: a Dead Letter Queue past
    `max_attempts`, and a `run_at` delay for scheduled execution."""

    id: str
    queue_name: str
    priority: int = 0
    status: AsyncJobStatus = AsyncJobStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    timeout_seconds: float = 30.0
    run_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    dead_letter_reason: str | None = None
