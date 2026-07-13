from typing import Protocol

from tmis.runtime_platform.event_store.schemas import StoredEvent, StreamSnapshot


class EventStreamStorePort(Protocol):
    def append(self, event: StoredEvent) -> None: ...

    def read_stream(self, stream_id: str, *, from_sequence: int = 0) -> list[StoredEvent]: ...

    def stream_ids(self) -> list[str]: ...


class SnapshotStorePort(Protocol):
    def save(self, snapshot: StreamSnapshot) -> None: ...

    def latest(self, stream_id: str) -> StreamSnapshot | None: ...
