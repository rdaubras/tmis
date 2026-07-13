from tmis.runtime_platform.event_store.ports import EventStreamStorePort, SnapshotStorePort
from tmis.runtime_platform.event_store.schemas import StoredEvent, StreamSnapshot


class ArchivedStreamError(RuntimeError):
    pass


class EventStoreEngine:
    """The Sprint 23 Phase 1 audit found no Event Sourcing
    implementation anywhere in TMIS — every `EventStore`-named class
    found by search is a plain operational-telemetry list (metrics,
    alerts, errors), not an append-only per-aggregate log. This is a
    new, generic implementation: `stream_id` is any aggregate/firm/
    entity identity, `event_type`/`payload` are plain strings/dicts
    rather than a shared base class, so any of TMIS's seven existing
    event hierarchies can be appended here by a caller that converts
    its own dataclass event to `(event_type, payload)` first — no
    domain is forced to inherit from a new base type."""

    def __init__(self, events: EventStreamStorePort, snapshots: SnapshotStorePort) -> None:
        self._events = events
        self._snapshots = snapshots
        self._archived_streams: set[str] = set()
        self._sequence_counters: dict[str, int] = {}

    def append(self, stream_id: str, event_type: str, payload: dict[str, object]) -> StoredEvent:
        if stream_id in self._archived_streams:
            raise ArchivedStreamError(f"stream {stream_id} is archived; restore() first")
        sequence = self._sequence_counters.get(stream_id, 0) + 1
        self._sequence_counters[stream_id] = sequence
        event = StoredEvent(
            stream_id=stream_id, sequence=sequence, event_type=event_type, payload=payload
        )
        self._events.append(event)
        return event

    def read_stream(self, stream_id: str, *, from_sequence: int = 0) -> list[StoredEvent]:
        return self._events.read_stream(stream_id, from_sequence=from_sequence)

    def snapshot(self, stream_id: str, state: dict[str, object]) -> StreamSnapshot:
        version = self._sequence_counters.get(stream_id, 0)
        snap = StreamSnapshot(stream_id=stream_id, version=version, state=state)
        self._snapshots.save(snap)
        return snap

    def latest_snapshot(self, stream_id: str) -> StreamSnapshot | None:
        return self._snapshots.latest(stream_id)

    def replay(self, stream_id: str) -> list[StoredEvent]:
        """The minimal event set a caller must fold to rebuild
        current state: everything since the latest snapshot, or the
        full stream if none exists yet."""
        snapshot = self._snapshots.latest(stream_id)
        from_sequence = snapshot.version if snapshot is not None else 0
        return self.read_stream(stream_id, from_sequence=from_sequence)

    def archive(self, stream_id: str) -> None:
        self._archived_streams.add(stream_id)

    def restore(self, stream_id: str) -> None:
        self._archived_streams.discard(stream_id)

    def is_archived(self, stream_id: str) -> bool:
        return stream_id in self._archived_streams
