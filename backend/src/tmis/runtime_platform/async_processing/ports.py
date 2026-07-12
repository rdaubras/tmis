from typing import Protocol

from tmis.runtime_platform.async_processing.schemas import AsyncJob


class AsyncJobStorePort(Protocol):
    def save(self, job: AsyncJob) -> None: ...

    def get(self, job_id: str) -> AsyncJob | None: ...

    def all(self) -> list[AsyncJob]: ...
