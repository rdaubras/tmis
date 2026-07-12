from datetime import UTC, datetime

from tmis.integration_hub.queue.schemas import QueueItem, QueueItemStatus

_RUNNABLE = frozenset({QueueItemStatus.PENDING, QueueItemStatus.RETRYING})


class InMemorySyncQueue:
    """Implements `SyncQueuePort`: priority-ordered, in-memory, with
    retry and timeout handling — same shape as
    `ai_team.work_queue.InMemoryWorkQueue`, reimplemented locally
    since the LIH is a distinct bounded context. `dequeue_next` only
    *selects* a candidate; the caller must still call
    `mark_running`/`mark_done`/`mark_failed` explicitly, keeping
    progress tracking unambiguous under retries."""

    def __init__(self) -> None:
        self._items: dict[str, QueueItem] = {}

    def enqueue(self, item: QueueItem) -> None:
        self._items[item.id] = item

    def dequeue_next(self) -> QueueItem | None:
        candidates = [item for item in self._items.values() if item.status in _RUNNABLE]
        if not candidates:
            return None
        candidates.sort(key=lambda item: (-item.priority, item.created_at))
        return candidates[0]

    def mark_running(self, item_id: str) -> None:
        item = self._items[item_id]
        item.status = QueueItemStatus.RUNNING
        item.attempts += 1
        item.started_at = datetime.now(UTC)

    def mark_done(self, item_id: str, detail: str) -> None:
        item = self._items[item_id]
        item.status = QueueItemStatus.DONE
        item.detail = detail
        item.completed_at = datetime.now(UTC)

    def mark_failed(self, item_id: str, error: str) -> QueueItem:
        item = self._items[item_id]
        item.error = error
        if item.attempts < item.max_attempts:
            item.status = QueueItemStatus.RETRYING
        else:
            item.status = QueueItemStatus.FAILED
            item.completed_at = datetime.now(UTC)
        return item

    def cancel(self, item_id: str) -> None:
        item = self._items[item_id]
        item.status = QueueItemStatus.CANCELLED
        item.completed_at = datetime.now(UTC)

    def get(self, item_id: str) -> QueueItem | None:
        return self._items.get(item_id)

    def list_all(self) -> list[QueueItem]:
        return list(self._items.values())

    def check_timeouts(self) -> list[QueueItem]:
        now = datetime.now(UTC)
        timed_out: list[QueueItem] = []
        for item in self._items.values():
            if item.status is not QueueItemStatus.RUNNING or item.started_at is None:
                continue
            elapsed = (now - item.started_at).total_seconds()
            if elapsed <= item.timeout_seconds:
                continue
            failed_item = self.mark_failed(item.id, f"timed out after {elapsed:.1f}s")
            if failed_item.status is QueueItemStatus.FAILED:
                failed_item.status = QueueItemStatus.TIMED_OUT
            timed_out.append(failed_item)
        return timed_out
