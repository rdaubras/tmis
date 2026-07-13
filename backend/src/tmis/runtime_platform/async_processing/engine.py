from datetime import UTC, datetime, timedelta

from tmis.runtime_platform.async_processing.ports import AsyncJobStorePort
from tmis.runtime_platform.async_processing.schemas import AsyncJob, AsyncJobStatus

_RUNNABLE = frozenset({AsyncJobStatus.PENDING, AsyncJobStatus.RETRYING})


class AsyncProcessingEngine:
    """Priority queue with the two capabilities the Sprint 23 Phase 1
    audit confirmed were missing from every existing in-memory queue
    in TMIS (`ai_team.work_queue`, `integration_hub.queue`): a Dead
    Letter Queue for jobs that exhaust their retries, and a `run_at`
    delay for scheduled execution. Retry/timeout/priority handling
    otherwise follows the same shape as those two engines, on
    purpose, so a caller already familiar with one recognizes the
    other immediately."""

    def __init__(self, store: AsyncJobStorePort, base_delay_seconds: float = 0.5) -> None:
        self._store = store
        self._base_delay_seconds = base_delay_seconds

    def enqueue(self, job: AsyncJob, *, delay_seconds: float = 0.0) -> AsyncJob:
        if delay_seconds > 0:
            job.run_at = datetime.now(UTC) + timedelta(seconds=delay_seconds)
            job.status = AsyncJobStatus.SCHEDULED
        self._store.save(job)
        return job

    def dequeue_ready(self, *, now: datetime | None = None) -> AsyncJob | None:
        now = now or datetime.now(UTC)

        def _is_ready(job: AsyncJob) -> bool:
            if job.status in _RUNNABLE:
                return True
            return (
                job.status is AsyncJobStatus.SCHEDULED
                and job.run_at is not None
                and job.run_at <= now
            )

        candidates = [job for job in self._store.all() if _is_ready(job)]
        if not candidates:
            return None
        candidates.sort(key=lambda job: (-job.priority, job.created_at))
        return candidates[0]

    def mark_running(self, job_id: str) -> None:
        job = self._require(job_id)
        job.status = AsyncJobStatus.RUNNING
        job.attempts += 1
        job.started_at = datetime.now(UTC)
        self._store.save(job)

    def mark_done(self, job_id: str) -> None:
        job = self._require(job_id)
        job.status = AsyncJobStatus.DONE
        job.completed_at = datetime.now(UTC)
        self._store.save(job)

    def mark_failed(self, job_id: str, error: str) -> AsyncJob:
        """Exponential backoff up to `max_attempts`; past that, the
        job moves to the Dead Letter Queue instead of being retried
        forever or silently dropped."""
        job = self._require(job_id)
        job.error = error
        if job.attempts < job.max_attempts:
            job.status = AsyncJobStatus.RETRYING
            delay = self._base_delay_seconds * (2**job.attempts)
            job.run_at = datetime.now(UTC) + timedelta(seconds=delay)
        else:
            job.status = AsyncJobStatus.DEAD_LETTERED
            job.dead_letter_reason = error
            job.completed_at = datetime.now(UTC)
        self._store.save(job)
        return job

    def cancel(self, job_id: str) -> None:
        job = self._require(job_id)
        job.status = AsyncJobStatus.CANCELLED
        job.completed_at = datetime.now(UTC)
        self._store.save(job)

    def check_timeouts(self, *, now: datetime | None = None) -> list[AsyncJob]:
        now = now or datetime.now(UTC)
        timed_out: list[AsyncJob] = []
        for job in self._store.all():
            if job.status is not AsyncJobStatus.RUNNING or job.started_at is None:
                continue
            if (now - job.started_at).total_seconds() <= job.timeout_seconds:
                continue
            failed = self.mark_failed(job.id, f"timed out after {job.timeout_seconds:.1f}s")
            if failed.status is AsyncJobStatus.DEAD_LETTERED:
                failed.dead_letter_reason = "timeout"
            timed_out.append(failed)
        return timed_out

    def dead_letters(self, *, queue_name: str | None = None) -> list[AsyncJob]:
        jobs = [j for j in self._store.all() if j.status is AsyncJobStatus.DEAD_LETTERED]
        if queue_name is not None:
            jobs = [j for j in jobs if j.queue_name == queue_name]
        return jobs

    def _require(self, job_id: str) -> AsyncJob:
        job = self._store.get(job_id)
        if job is None:
            raise KeyError(job_id)
        return job
