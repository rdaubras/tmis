from datetime import UTC, datetime, timedelta

from tmis.collaboration.presence.schemas import OptimisticLock


class InMemoryOptimisticLockService:
    """Implements `OptimisticLockPort`: an advisory, non-blocking lock —
    it only lets a caller detect that someone else is already editing
    the same target and surface a conflict; it cannot prevent a client
    from writing anyway (see docs/33-legal-collaboration.md — Presence
    Engine)."""

    def __init__(self) -> None:
        self._locks: dict[tuple[str, str], OptimisticLock] = {}

    def acquire(
        self,
        target_type: str,
        target_id: str,
        member_id: str,
        ttl_seconds: int | None = None,
    ) -> OptimisticLock:
        existing = self.current(target_type, target_id)
        if existing is not None and existing.locked_by != member_id:
            raise ValueError(
                f"{target_type}:{target_id} is already locked by {existing.locked_by!r}"
            )
        now = datetime.now(UTC)
        lock = OptimisticLock(
            target_type=target_type,
            target_id=target_id,
            locked_by=member_id,
            acquired_at=now,
            expires_at=now + timedelta(seconds=ttl_seconds) if ttl_seconds is not None else None,
        )
        self._locks[(target_type, target_id)] = lock
        return lock

    def release(self, target_type: str, target_id: str, member_id: str) -> None:
        lock = self._locks.get((target_type, target_id))
        if lock is None:
            return
        if lock.locked_by != member_id:
            raise ValueError(
                f"{target_type}:{target_id} is locked by {lock.locked_by!r}, not {member_id!r}"
            )
        del self._locks[(target_type, target_id)]

    def current(self, target_type: str, target_id: str) -> OptimisticLock | None:
        lock = self._locks.get((target_type, target_id))
        if lock is None:
            return None
        if lock.expires_at is not None and lock.expires_at < datetime.now(UTC):
            del self._locks[(target_type, target_id)]
            return None
        return lock
