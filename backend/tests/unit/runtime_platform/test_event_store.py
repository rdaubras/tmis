import pytest

from tmis.runtime_platform.event_store.engine import ArchivedStreamError, EventStoreEngine
from tmis.runtime_platform.event_store.store import InMemoryEventStreamStore, InMemorySnapshotStore


def _engine() -> EventStoreEngine:
    return EventStoreEngine(InMemoryEventStreamStore(), InMemorySnapshotStore())


def test_append_assigns_incrementing_sequence_per_stream() -> None:
    engine = _engine()
    e1 = engine.append("firm-1", "Created", {"name": "Acme"})
    e2 = engine.append("firm-1", "Renamed", {"name": "Acme Corp"})
    other = engine.append("firm-2", "Created", {"name": "Beta"})

    assert e1.sequence == 1
    assert e2.sequence == 2
    assert other.sequence == 1


def test_read_stream_from_sequence() -> None:
    engine = _engine()
    engine.append("firm-1", "A", {})
    engine.append("firm-1", "B", {})
    engine.append("firm-1", "C", {})

    events = engine.read_stream("firm-1", from_sequence=1)
    assert [e.event_type for e in events] == ["B", "C"]


def test_replay_only_events_since_latest_snapshot() -> None:
    engine = _engine()
    engine.append("firm-1", "A", {})
    engine.append("firm-1", "B", {})
    engine.snapshot("firm-1", {"count": 2})
    engine.append("firm-1", "C", {})

    replayed = engine.replay("firm-1")
    assert [e.event_type for e in replayed] == ["C"]


def test_latest_snapshot_returns_highest_version() -> None:
    engine = _engine()
    engine.append("firm-1", "A", {})
    first = engine.snapshot("firm-1", {"count": 1})
    engine.append("firm-1", "B", {})
    second = engine.snapshot("firm-1", {"count": 2})

    latest = engine.latest_snapshot("firm-1")
    assert latest is not None
    assert latest.version == second.version
    assert latest.version > first.version


def test_archived_stream_rejects_further_appends() -> None:
    engine = _engine()
    engine.append("firm-1", "A", {})
    engine.archive("firm-1")

    assert engine.is_archived("firm-1") is True
    with pytest.raises(ArchivedStreamError):
        engine.append("firm-1", "B", {})


def test_restore_allows_appends_again() -> None:
    engine = _engine()
    engine.append("firm-1", "A", {})
    engine.archive("firm-1")
    engine.restore("firm-1")

    assert engine.is_archived("firm-1") is False
    event = engine.append("firm-1", "B", {})
    assert event.sequence == 2
