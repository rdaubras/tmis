from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MemberStatus(str, Enum):
    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


@dataclass(frozen=True, slots=True)
class MemberHistoryEntry:
    timestamp: datetime
    from_status: MemberStatus | None
    to_status: MemberStatus
    actor_id: str | None


@dataclass(slots=True)
class Member:
    """One person in a workspace — an invitation, and everything that
    happened to it since (see docs/33-legal-collaboration.md — Members
    Engine). `history` is append-only: a status change never erases the
    ones before it."""

    id: str
    workspace_id: str
    email: str
    display_name: str
    status: MemberStatus = MemberStatus.INVITED
    invited_at: datetime | None = None
    activated_at: datetime | None = None
    history: list[MemberHistoryEntry] = field(default_factory=list)
