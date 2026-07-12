from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class StoredEvent:
    """One append-only entry in a stream (an aggregate's history, a
    firm's audit trail, anything with an identity worth replaying).
    `event_type`/`payload` are plain strings/dicts rather than a
    typed base class, deliberately — see `engine.py` docstring for
    why: it lets this store accept events from any of TMIS's seven
    existing hand-rolled event hierarchies without forcing them onto
    a shared base class."""

    stream_id: str
    sequence: int
    event_type: str
    payload: dict[str, Any]
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class StreamSnapshot:
    stream_id: str
    version: int
    state: dict[str, Any]
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
