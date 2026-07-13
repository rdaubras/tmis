from tmis.runtime_platform.event_store.schemas import StoredEvent, StreamSnapshot


class InMemoryEventStreamStore:
    def __init__(self) -> None:
        self._streams: dict[str, list[StoredEvent]] = {}

    def append(self, event: StoredEvent) -> None:
        self._streams.setdefault(event.stream_id, []).append(event)

    def read_stream(self, stream_id: str, *, from_sequence: int = 0) -> list[StoredEvent]:
        return [e for e in self._streams.get(stream_id, []) if e.sequence > from_sequence]

    def stream_ids(self) -> list[str]:
        return list(self._streams.keys())


class InMemorySnapshotStore:
    def __init__(self) -> None:
        self._snapshots: dict[str, list[StreamSnapshot]] = {}

    def save(self, snapshot: StreamSnapshot) -> None:
        self._snapshots.setdefault(snapshot.stream_id, []).append(snapshot)

    def latest(self, stream_id: str) -> StreamSnapshot | None:
        snapshots = self._snapshots.get(stream_id)
        if not snapshots:
            return None
        return max(snapshots, key=lambda s: s.version)
