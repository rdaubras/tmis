from datetime import UTC, datetime, timedelta

import pytest

from tmis.integration_hub.queue import InMemorySyncQueue, QueueItem
from tmis.integration_hub.retry import IntegrationRetryPolicy
from tmis.integration_hub.scheduler import InMemorySyncSchedulerStore, SyncSchedulerEngine


def test_sync_queue_dequeue_priority_order() -> None:
    queue = InMemorySyncQueue()
    queue.enqueue(QueueItem(id="q-1", firm_id="f1", job_id="j1", priority=1))
    queue.enqueue(QueueItem(id="q-2", firm_id="f1", job_id="j2", priority=5))
    next_item = queue.dequeue_next()
    assert next_item is not None
    assert next_item.id == "q-2"


def test_sync_queue_mark_running_done() -> None:
    queue = InMemorySyncQueue()
    queue.enqueue(QueueItem(id="q-1", firm_id="f1", job_id="j1"))
    queue.mark_running("q-1")
    item = queue.get("q-1")
    assert item is not None
    assert item.status.value == "running"
    assert item.attempts == 1

    queue.mark_done("q-1", "ok")
    item = queue.get("q-1")
    assert item is not None
    assert item.status.value == "done"
    assert item.detail == "ok"


def test_sync_queue_mark_failed_retries_then_fails() -> None:
    queue = InMemorySyncQueue()
    queue.enqueue(QueueItem(id="q-1", firm_id="f1", job_id="j1", max_attempts=1))
    queue.mark_running("q-1")
    failed = queue.mark_failed("q-1", "boom")
    assert failed.status.value == "failed"


def test_sync_queue_cancel() -> None:
    queue = InMemorySyncQueue()
    queue.enqueue(QueueItem(id="q-1", firm_id="f1", job_id="j1"))
    queue.cancel("q-1")
    item = queue.get("q-1")
    assert item is not None
    assert item.status.value == "cancelled"


def test_sync_queue_check_timeouts() -> None:
    queue = InMemorySyncQueue()
    item = QueueItem(id="q-1", firm_id="f1", job_id="j1", timeout_seconds=0.0, max_attempts=1)
    queue.enqueue(item)
    queue.mark_running("q-1")
    item.started_at = datetime.now(UTC) - timedelta(seconds=10)

    timed_out = queue.check_timeouts()
    assert len(timed_out) == 1
    assert timed_out[0].status.value == "timed_out"


def test_sync_scheduler_schedule_and_due() -> None:
    store = InMemorySyncSchedulerStore()
    scheduler = SyncSchedulerEngine(store)
    past = datetime.now(UTC) - timedelta(minutes=1)
    scheduled = scheduler.schedule("f1", "job-1", past, interval=timedelta(minutes=15))

    due = scheduler.due("f1", datetime.now(UTC))
    assert due == [scheduled]

    scheduler.mark_fired(scheduled, datetime.now(UTC))
    assert scheduled.next_fire_at > datetime.now(UTC)


def test_sync_scheduler_not_due_yet() -> None:
    store = InMemorySyncSchedulerStore()
    scheduler = SyncSchedulerEngine(store)
    future = datetime.now(UTC) + timedelta(hours=1)
    scheduler.schedule("f1", "job-1", future)
    assert scheduler.due("f1", datetime.now(UTC)) == []


@pytest.mark.asyncio
async def test_retry_policy_succeeds_after_transient_failures() -> None:
    policy = IntegrationRetryPolicy(max_attempts=3, base_delay_seconds=0.001)
    attempts = 0

    async def flaky() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("boom")
        return "ok"

    result = await policy.run(flaky)
    assert result == "ok"
    assert attempts == 3


@pytest.mark.asyncio
async def test_retry_policy_exhausts_attempts_and_raises() -> None:
    policy = IntegrationRetryPolicy(max_attempts=2, base_delay_seconds=0.001)

    async def always_fails() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        await policy.run(always_fails)
