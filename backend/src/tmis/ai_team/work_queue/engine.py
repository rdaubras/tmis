from datetime import UTC, datetime

from tmis.ai.schemas.agent import AgentOutput
from tmis.ai_team.work_queue.schemas import WorkItem, WorkItemStatus

_RUNNABLE = frozenset({WorkItemStatus.PENDING, WorkItemStatus.RETRYING})


class InMemoryWorkQueue:
    """Implements `WorkQueuePort` (see docs/55-guide-coordinateur.md —
    Work Queue): priority-ordered, in-memory, with retry and timeout
    handling. `dequeue_next` only *selects* a candidate — it does not
    itself mutate state — so a caller sees an explicit
    `mark_running`/`mark_done`/`mark_failed` transition for every item,
    which keeps progress tracking unambiguous even under retries."""

    def __init__(self) -> None:
        self._items: dict[str, WorkItem] = {}

    def enqueue(self, item: WorkItem) -> None:
        self._items[item.id] = item

    def dequeue_next(self) -> WorkItem | None:
        candidates = [item for item in self._items.values() if item.status in _RUNNABLE]
        if not candidates:
            return None
        candidates.sort(key=lambda item: (-item.priority, item.created_at))
        return candidates[0]

    def mark_running(self, item_id: str) -> None:
        item = self._items[item_id]
        item.status = WorkItemStatus.RUNNING
        item.attempts += 1
        item.started_at = datetime.now(UTC)

    def mark_done(self, item_id: str, result: AgentOutput) -> None:
        item = self._items[item_id]
        item.status = WorkItemStatus.DONE
        item.result = result
        item.completed_at = datetime.now(UTC)

    def mark_failed(self, item_id: str, error: str) -> WorkItem:
        item = self._items[item_id]
        item.error = error
        if item.attempts < item.max_attempts:
            item.status = WorkItemStatus.RETRYING
        else:
            item.status = WorkItemStatus.FAILED
            item.completed_at = datetime.now(UTC)
        return item

    def cancel(self, item_id: str) -> None:
        item = self._items[item_id]
        item.status = WorkItemStatus.CANCELLED
        item.completed_at = datetime.now(UTC)

    def get(self, item_id: str) -> WorkItem | None:
        return self._items.get(item_id)

    def list_all(self) -> list[WorkItem]:
        return list(self._items.values())

    def check_timeouts(self) -> list[WorkItem]:
        now = datetime.now(UTC)
        timed_out: list[WorkItem] = []
        for item in self._items.values():
            if item.status is not WorkItemStatus.RUNNING or item.started_at is None:
                continue
            elapsed = (now - item.started_at).total_seconds()
            if elapsed <= item.timeout_seconds:
                continue
            failed_item = self.mark_failed(item.id, f"timed out after {elapsed:.1f}s")
            if failed_item.status is WorkItemStatus.FAILED:
                failed_item.status = WorkItemStatus.TIMED_OUT
            timed_out.append(failed_item)
        return timed_out
