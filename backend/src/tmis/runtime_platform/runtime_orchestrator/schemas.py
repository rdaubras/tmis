import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class RuntimeTaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


def new_runtime_task_id() -> str:
    return f"rt-{uuid.uuid4().hex[:12]}"


@dataclass(slots=True)
class RuntimeTask:
    """A long-running unit of work supervised by the
    `RuntimeOrchestrator`. Generalizes the single-level
    `depends_on`/priority pattern already used by
    `ai_team.coordinator`/`ai_team.work_queue` into a domain-agnostic
    shape any bounded context can submit work through, instead of
    every context hand-rolling its own dependency check."""

    id: str
    name: str
    priority: int = 0
    depends_on: frozenset[str] = field(default_factory=frozenset)
    status: RuntimeTaskStatus = RuntimeTaskStatus.PENDING
    checkpoint: int = 0
    firm_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
