import pytest

from tmis.collaboration.members.schemas import MemberStatus
from tmis.collaboration.members.service import MemberService


def test_invite_creates_a_member_in_invited_status_with_one_history_entry() -> None:
    service = MemberService()
    member = service.invite("ws-1", "avocat@cabinet.fr", "Jane Avocat")

    assert member.status is MemberStatus.INVITED
    assert len(member.history) == 1
    assert member.history[0].from_status is None
    assert member.history[0].to_status is MemberStatus.INVITED


def test_activate_transitions_invited_to_active_and_sets_activated_at() -> None:
    service = MemberService()
    member = service.invite("ws-1", "avocat@cabinet.fr", "Jane Avocat")

    activated = service.activate(member.id, actor_id="admin-1")

    assert activated.status is MemberStatus.ACTIVE
    assert activated.activated_at is not None
    assert len(activated.history) == 2
    assert activated.history[-1].actor_id == "admin-1"


def test_history_is_append_only_never_overwritten() -> None:
    service = MemberService()
    member = service.invite("ws-1", "avocat@cabinet.fr", "Jane Avocat")
    service.activate(member.id)
    service.suspend(member.id)
    reactivated = service.reactivate(member.id)

    assert len(reactivated.history) == 4
    assert [e.to_status for e in reactivated.history] == [
        MemberStatus.INVITED,
        MemberStatus.ACTIVE,
        MemberStatus.SUSPENDED,
        MemberStatus.ACTIVE,
    ]


def test_cannot_activate_a_deactivated_member() -> None:
    service = MemberService()
    member = service.invite("ws-1", "avocat@cabinet.fr", "Jane Avocat")
    service.deactivate(member.id)

    with pytest.raises(ValueError, match="Cannot transition"):
        service.activate(member.id)


def test_deactivated_is_a_terminal_status() -> None:
    service = MemberService()
    member = service.invite("ws-1", "avocat@cabinet.fr", "Jane Avocat")
    service.activate(member.id)
    service.deactivate(member.id)

    with pytest.raises(ValueError):
        service.suspend(member.id)


def test_cannot_suspend_an_invited_member_directly() -> None:
    service = MemberService()
    member = service.invite("ws-1", "avocat@cabinet.fr", "Jane Avocat")

    with pytest.raises(ValueError):
        service.suspend(member.id)


def test_transition_on_unknown_member_raises() -> None:
    service = MemberService()

    with pytest.raises(ValueError, match="Unknown member"):
        service.activate("does-not-exist")
