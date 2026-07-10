import time

import pytest

from tmis.collaboration.audit.store import InMemoryAuditStore
from tmis.collaboration.audit.trail import AuditTrail
from tmis.collaboration.presence.locking import InMemoryOptimisticLockService
from tmis.collaboration.presence.schemas import PresenceStatus
from tmis.collaboration.presence.service import InMemoryPresenceTracker
from tmis.collaboration.sharing.engine import SharingEngine
from tmis.collaboration.sharing.schemas import SharePermission
from tmis.collaboration.sharing.store import InMemorySharingStore


def test_presence_heartbeat_and_list_online() -> None:
    tracker = InMemoryPresenceTracker()
    tracker.heartbeat("ws-1", "member-1", PresenceStatus.ONLINE, "document", "doc-1")
    tracker.heartbeat("ws-1", "member-2", PresenceStatus.OFFLINE)

    online = tracker.list_online("ws-1")

    assert len(online) == 1
    assert online[0].member_id == "member-1"


def test_presence_viewers_returns_non_offline_viewers_of_a_target() -> None:
    tracker = InMemoryPresenceTracker()
    tracker.heartbeat("ws-1", "member-1", PresenceStatus.ONLINE, "document", "doc-1")
    tracker.heartbeat("ws-1", "member-2", PresenceStatus.IDLE, "document", "doc-1")
    tracker.heartbeat("ws-1", "member-3", PresenceStatus.OFFLINE, "document", "doc-1")

    viewers = tracker.viewers("document", "doc-1")

    assert {v.member_id for v in viewers} == {"member-1", "member-2"}


def test_optimistic_lock_acquire_then_release() -> None:
    locks = InMemoryOptimisticLockService()
    lock = locks.acquire("document", "doc-1", "member-1")

    assert lock.locked_by == "member-1"
    assert locks.current("document", "doc-1") is not None

    locks.release("document", "doc-1", "member-1")

    assert locks.current("document", "doc-1") is None


def test_optimistic_lock_blocks_a_different_member() -> None:
    locks = InMemoryOptimisticLockService()
    locks.acquire("document", "doc-1", "member-1")

    with pytest.raises(ValueError, match="already locked"):
        locks.acquire("document", "doc-1", "member-2")


def test_optimistic_lock_reacquire_by_same_member_is_allowed() -> None:
    locks = InMemoryOptimisticLockService()
    locks.acquire("document", "doc-1", "member-1")
    lock = locks.acquire("document", "doc-1", "member-1")

    assert lock.locked_by == "member-1"


def test_optimistic_lock_release_by_wrong_member_raises() -> None:
    locks = InMemoryOptimisticLockService()
    locks.acquire("document", "doc-1", "member-1")

    with pytest.raises(ValueError, match="is locked by"):
        locks.release("document", "doc-1", "member-2")


def test_optimistic_lock_expires_and_can_be_reacquired() -> None:
    locks = InMemoryOptimisticLockService()
    locks.acquire("document", "doc-1", "member-1", ttl_seconds=0)
    time.sleep(0.01)

    assert locks.current("document", "doc-1") is None

    lock = locks.acquire("document", "doc-1", "member-2")
    assert lock.locked_by == "member-2"


def test_release_of_an_unlocked_target_is_a_no_op() -> None:
    locks = InMemoryOptimisticLockService()
    locks.release("document", "doc-1", "member-1")


def test_sharing_engine_create_link_and_resolve() -> None:
    engine = SharingEngine(InMemorySharingStore())
    link = engine.create_link("ws-1", "document", "doc-1", SharePermission.READ, "member-1")

    resolved = engine.resolve_link(link.token)

    assert resolved is not None
    assert resolved.target_id == "doc-1"


def test_sharing_engine_revoke_link_makes_it_unresolvable() -> None:
    engine = SharingEngine(InMemorySharingStore())
    link = engine.create_link("ws-1", "document", "doc-1", SharePermission.READ, "member-1")

    engine.revoke_link(link.token)

    assert engine.resolve_link(link.token) is None


def test_sharing_engine_expired_link_is_unresolvable() -> None:
    engine = SharingEngine(InMemorySharingStore())
    link = engine.create_link(
        "ws-1", "document", "doc-1", SharePermission.READ, "member-1", expires_in_seconds=0
    )
    time.sleep(0.01)

    assert engine.resolve_link(link.token) is None


def test_sharing_engine_unknown_token_resolves_to_none() -> None:
    engine = SharingEngine(InMemorySharingStore())

    assert engine.resolve_link("does-not-exist") is None


def test_sharing_engine_revoke_unknown_token_raises() -> None:
    engine = SharingEngine(InMemorySharingStore())

    with pytest.raises(ValueError, match="Unknown share link"):
        engine.revoke_link("does-not-exist")


def test_sharing_engine_share_internally_and_list_for_target() -> None:
    engine = SharingEngine(InMemorySharingStore())
    engine.share_internally(
        "ws-1", "document", "doc-1", "member-2", SharePermission.COMMENT, "member-1"
    )

    shares = engine.list_for_target("document", "doc-1")

    assert len(shares) == 1
    assert shares[0].shared_with_member_id == "member-2"


def test_audit_trail_records_old_and_new_state() -> None:
    trail = AuditTrail(InMemoryAuditStore())
    trail.record(
        "ws-1", "actor-1", "task.status_change", "task", "t1",
        old_state={"status": "todo"}, new_state={"status": "in_progress"},
        ip_address="203.0.113.4",
    )

    entries = trail.list_for_workspace("ws-1")

    assert len(entries) == 1
    assert entries[0].old_state == {"status": "todo"}
    assert entries[0].new_state == {"status": "in_progress"}
    assert entries[0].ip_address == "203.0.113.4"


def test_audit_trail_list_for_target() -> None:
    trail = AuditTrail(InMemoryAuditStore())
    trail.record("ws-1", "actor-1", "task.create", "task", "t1")
    trail.record("ws-1", "actor-1", "task.create", "task", "t2")

    entries = trail.list_for_target("task", "t1")

    assert len(entries) == 1
    assert entries[0].target_id == "t1"
