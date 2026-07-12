from typing import Protocol

from tmis.cloud_operations.error_tracking.schemas import ErrorEvent


class ErrorEventStorePort(Protocol):
    def save(self, event: ErrorEvent) -> None: ...

    def list_recent(self, limit: int) -> list[ErrorEvent]: ...

    def list_for_source(self, source: str) -> list[ErrorEvent]: ...
