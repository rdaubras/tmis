from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class PresenceStatus(str, Enum):
    ONLINE = "online"
    IDLE = "idle"
    OFFLINE = "offline"


@dataclass(frozen=True, slots=True)
class PresenceInfo:
    """A member's last-known presence (see docs/33-legal-collaboration.md
    — Presence Engine, architecture-only per the sprint brief: no
    real-time transport is implemented here, only the shape a future
    websocket/pubsub layer would populate)."""

    workspace_id: str
    member_id: str
    status: PresenceStatus
    target_type: str | None
    target_id: str | None
    last_seen_at: datetime


@dataclass(frozen=True, slots=True)
class OptimisticLock:
    """A non-blocking edit lock on one target — advisory: nothing
    prevents a second writer, but callers can detect and surface the
    conflict (see docs/33-legal-collaboration.md — Presence Engine)."""

    target_type: str
    target_id: str
    locked_by: str
    acquired_at: datetime
    expires_at: datetime | None
