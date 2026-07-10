from typing import Protocol

from tmis.collaboration.presence.schemas import OptimisticLock, PresenceInfo, PresenceStatus


class PresencePort(Protocol):
    """Port implemented by every interchangeable presence tracker.
    Architecture only, per the sprint brief — this reference
    implementation is a plain in-memory heartbeat, not a real-time
    transport."""

    def heartbeat(
        self,
        workspace_id: str,
        member_id: str,
        status: PresenceStatus,
        target_type: str | None = None,
        target_id: str | None = None,
    ) -> PresenceInfo: ...

    def list_online(self, workspace_id: str) -> list[PresenceInfo]: ...

    def viewers(self, target_type: str, target_id: str) -> list[PresenceInfo]: ...


class OptimisticLockPort(Protocol):
    """Port implemented by every interchangeable optimistic-locking
    service (see docs/33-legal-collaboration.md — Presence Engine)."""

    def acquire(
        self,
        target_type: str,
        target_id: str,
        member_id: str,
        ttl_seconds: int | None = None,
    ) -> OptimisticLock: ...

    def release(self, target_type: str, target_id: str, member_id: str) -> None: ...

    def current(self, target_type: str, target_id: str) -> OptimisticLock | None: ...
