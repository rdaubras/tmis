from tmis.integration_hub.synchronization.schemas import SyncJobConfig


class InMemorySyncJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, SyncJobConfig] = {}

    def save(self, job: SyncJobConfig) -> None:
        self._jobs[job.id] = job

    def get(self, firm_id: str, job_id: str) -> SyncJobConfig | None:
        job = self._jobs.get(job_id)
        if job is None or job.firm_id != firm_id:
            return None
        return job

    def list_all(self, firm_id: str) -> list[SyncJobConfig]:
        return [job for job in self._jobs.values() if job.firm_id == firm_id]
