import uuid
from datetime import UTC, datetime

from tmis.collaboration.members.ports import MemberStorePort
from tmis.collaboration.members.schemas import Member, MemberHistoryEntry, MemberStatus
from tmis.collaboration.members.store import InMemoryMemberStore

_ALLOWED_TRANSITIONS: dict[MemberStatus, set[MemberStatus]] = {
    MemberStatus.INVITED: {MemberStatus.ACTIVE, MemberStatus.DEACTIVATED},
    MemberStatus.ACTIVE: {MemberStatus.SUSPENDED, MemberStatus.DEACTIVATED},
    MemberStatus.SUSPENDED: {MemberStatus.ACTIVE, MemberStatus.DEACTIVATED},
    MemberStatus.DEACTIVATED: set(),
}


class MemberService:
    """Implements `MemberServicePort`: invitation, activation,
    suspension, deactivation, reactivation — every transition checked
    against `_ALLOWED_TRANSITIONS` and appended to `Member.history`,
    never overwriting a previous entry (see
    docs/33-legal-collaboration.md — Members Engine)."""

    def __init__(self, store: MemberStorePort | None = None) -> None:
        self._store: MemberStorePort = store or InMemoryMemberStore()

    def invite(self, workspace_id: str, email: str, display_name: str) -> Member:
        now = datetime.now(UTC)
        member = Member(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            email=email,
            display_name=display_name,
            status=MemberStatus.INVITED,
            invited_at=now,
            history=[
                MemberHistoryEntry(
                    timestamp=now, from_status=None, to_status=MemberStatus.INVITED, actor_id=None
                )
            ],
        )
        self._store.save(member)
        return member

    def activate(self, member_id: str, actor_id: str | None = None) -> Member:
        member = self._transition(member_id, MemberStatus.ACTIVE, actor_id)
        member.activated_at = datetime.now(UTC)
        self._store.save(member)
        return member

    def suspend(self, member_id: str, actor_id: str | None = None) -> Member:
        return self._transition(member_id, MemberStatus.SUSPENDED, actor_id)

    def deactivate(self, member_id: str, actor_id: str | None = None) -> Member:
        return self._transition(member_id, MemberStatus.DEACTIVATED, actor_id)

    def reactivate(self, member_id: str, actor_id: str | None = None) -> Member:
        return self._transition(member_id, MemberStatus.ACTIVE, actor_id)

    def _transition(self, member_id: str, to_status: MemberStatus, actor_id: str | None) -> Member:
        member = self._store.get(member_id)
        if member is None:
            raise ValueError(f"Unknown member {member_id!r}")
        allowed = _ALLOWED_TRANSITIONS.get(member.status, set())
        if to_status not in allowed:
            raise ValueError(f"Cannot transition member from {member.status} to {to_status}")
        member.history.append(
            MemberHistoryEntry(
                timestamp=datetime.now(UTC),
                from_status=member.status,
                to_status=to_status,
                actor_id=actor_id,
            )
        )
        member.status = to_status
        self._store.save(member)
        return member
