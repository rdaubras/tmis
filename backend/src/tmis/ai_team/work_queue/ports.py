from typing import Protocol

from tmis.ai.schemas.agent import AgentOutput
from tmis.ai_team.work_queue.schemas import WorkItem


class WorkQueuePort(Protocol):
    """Port implemented by every interchangeable work queue (see
    docs/55-guide-coordinateur.md — Work Queue). The in-memory
    reference implementation and a future distributed one (Celery/
    Redis-backed) both satisfy this same contract, so the Coordinator
    never depends on which is wired in."""

    def enqueue(self, item: WorkItem) -> None: ...

    def dequeue_next(self) -> WorkItem | None: ...

    def mark_running(self, item_id: str) -> None: ...

    def mark_done(self, item_id: str, result: AgentOutput) -> None: ...

    def mark_failed(self, item_id: str, error: str) -> WorkItem: ...

    def cancel(self, item_id: str) -> None: ...

    def get(self, item_id: str) -> WorkItem | None: ...

    def list_all(self) -> list[WorkItem]: ...

    def check_timeouts(self) -> list[WorkItem]: ...
