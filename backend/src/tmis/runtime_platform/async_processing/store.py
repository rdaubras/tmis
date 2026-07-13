from tmis.runtime_platform.async_processing.schemas import AsyncJob


class InMemoryAsyncJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, AsyncJob] = {}

    def save(self, job: AsyncJob) -> None:
        self._jobs[job.id] = job

    def get(self, job_id: str) -> AsyncJob | None:
        return self._jobs.get(job_id)

    def all(self) -> list[AsyncJob]:
        return list(self._jobs.values())
