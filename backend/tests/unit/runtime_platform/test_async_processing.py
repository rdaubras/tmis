from datetime import UTC, datetime, timedelta

from tmis.runtime_platform.async_processing.engine import AsyncProcessingEngine
from tmis.runtime_platform.async_processing.schemas import AsyncJob, AsyncJobStatus
from tmis.runtime_platform.async_processing.store import InMemoryAsyncJobStore


def _engine() -> AsyncProcessingEngine:
    return AsyncProcessingEngine(InMemoryAsyncJobStore(), base_delay_seconds=0.1)


def test_enqueue_and_dequeue_by_priority() -> None:
    engine = _engine()
    engine.enqueue(AsyncJob(id="low", queue_name="q", priority=1))
    engine.enqueue(AsyncJob(id="high", queue_name="q", priority=10))

    assert engine.dequeue_ready().id == "high"


def test_delayed_job_not_ready_until_run_at() -> None:
    engine = _engine()
    engine.enqueue(AsyncJob(id="a", queue_name="q"), delay_seconds=60)

    assert engine.dequeue_ready() is None
    future = datetime.now(UTC) + timedelta(seconds=61)
    assert engine.dequeue_ready(now=future).id == "a"


def test_retries_then_moves_to_dead_letter_queue() -> None:
    engine = _engine()
    job = AsyncJob(id="a", queue_name="q", max_attempts=2)
    engine.enqueue(job)

    engine.mark_running("a")
    retried = engine.mark_failed("a", "boom-1")
    assert retried.status is AsyncJobStatus.RETRYING
    assert retried.run_at is not None

    engine.mark_running("a")
    dead = engine.mark_failed("a", "boom-2")
    assert dead.status is AsyncJobStatus.DEAD_LETTERED
    assert dead.dead_letter_reason == "boom-2"
    assert engine.dead_letters() == [dead]
    assert engine.dead_letters(queue_name="other") == []


def test_check_timeouts_moves_running_job_toward_dead_letter() -> None:
    engine = _engine()
    engine.enqueue(AsyncJob(id="a", queue_name="q", max_attempts=1, timeout_seconds=1.0))
    engine.mark_running("a")

    future = datetime.now(UTC) + timedelta(seconds=5)
    timed_out = engine.check_timeouts(now=future)
    assert len(timed_out) == 1
    assert timed_out[0].status is AsyncJobStatus.DEAD_LETTERED
    assert timed_out[0].dead_letter_reason == "timeout"


def test_cancel_marks_job_cancelled() -> None:
    engine = _engine()
    engine.enqueue(AsyncJob(id="a", queue_name="q"))
    engine.cancel("a")
    assert engine.dequeue_ready() is None
