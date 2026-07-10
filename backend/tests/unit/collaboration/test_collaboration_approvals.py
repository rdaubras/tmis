import pytest

from tmis.collaboration.approvals.engine import ApprovalEngine
from tmis.collaboration.approvals.schemas import ApprovalDecisionType, ApprovalMode, ApprovalStatus
from tmis.collaboration.approvals.store import InMemoryApprovalStore


def _engine() -> ApprovalEngine:
    return ApprovalEngine(InMemoryApprovalStore())


def test_request_starts_pending() -> None:
    engine = _engine()
    approval = engine.request(
        "ws-1", "document", "doc-1", "requester", ["approver-1"], ApprovalMode.SINGLE
    )

    assert approval.status is ApprovalStatus.PENDING
    assert approval.history == []


def test_single_mode_approved_after_one_approve() -> None:
    engine = _engine()
    approval = engine.request(
        "ws-1", "document", "doc-1", "requester", ["approver-1", "approver-2"], ApprovalMode.SINGLE
    )

    decided = engine.decide(approval.id, "approver-1", ApprovalDecisionType.APPROVE)

    assert decided.status is ApprovalStatus.APPROVED


def test_multiple_mode_requires_every_approver() -> None:
    engine = _engine()
    approval = engine.request(
        "ws-1", "document", "doc-1", "requester",
        ["approver-1", "approver-2"], ApprovalMode.MULTIPLE,
    )

    after_first = engine.decide(approval.id, "approver-1", ApprovalDecisionType.APPROVE)
    assert after_first.status is ApprovalStatus.PENDING

    after_second = engine.decide(approval.id, "approver-2", ApprovalDecisionType.APPROVE)
    assert after_second.status is ApprovalStatus.APPROVED


def test_a_single_rejection_blocks_multiple_mode_even_if_others_approved() -> None:
    engine = _engine()
    approval = engine.request(
        "ws-1", "document", "doc-1", "requester",
        ["approver-1", "approver-2"], ApprovalMode.MULTIPLE,
    )
    engine.decide(approval.id, "approver-1", ApprovalDecisionType.APPROVE)
    decided = engine.decide(approval.id, "approver-2", ApprovalDecisionType.REJECT)

    assert decided.status is ApprovalStatus.REJECTED


def test_rejection_overrides_an_earlier_approval_in_single_mode() -> None:
    """A rejection always dominates, regardless of mode: 'refus' must be
    able to override a prior 'validation simple' by another approver."""
    engine = _engine()
    approval = engine.request(
        "ws-1", "document", "doc-1", "requester",
        ["approver-1", "approver-2"], ApprovalMode.SINGLE,
    )
    engine.decide(approval.id, "approver-1", ApprovalDecisionType.APPROVE)
    decided = engine.decide(approval.id, "approver-2", ApprovalDecisionType.REJECT)

    assert decided.status is ApprovalStatus.REJECTED


def test_request_changes_sets_changes_requested_status() -> None:
    engine = _engine()
    approval = engine.request(
        "ws-1", "document", "doc-1", "requester", ["approver-1"], ApprovalMode.SINGLE
    )

    decided = engine.decide(
        approval.id, "approver-1", ApprovalDecisionType.REQUEST_CHANGES, "Revoir la clause 3"
    )

    assert decided.status is ApprovalStatus.CHANGES_REQUESTED
    assert decided.history[0].comment == "Revoir la clause 3"


def test_a_later_approval_can_resolve_a_change_request() -> None:
    engine = _engine()
    approval = engine.request(
        "ws-1", "document", "doc-1", "requester", ["approver-1"], ApprovalMode.SINGLE
    )
    engine.decide(approval.id, "approver-1", ApprovalDecisionType.REQUEST_CHANGES)
    decided = engine.decide(approval.id, "approver-1", ApprovalDecisionType.APPROVE)

    assert decided.status is ApprovalStatus.APPROVED


def test_history_is_append_only_and_keeps_every_decision() -> None:
    engine = _engine()
    approval = engine.request(
        "ws-1", "document", "doc-1", "requester", ["approver-1"], ApprovalMode.SINGLE
    )
    engine.decide(approval.id, "approver-1", ApprovalDecisionType.REQUEST_CHANGES)
    decided = engine.decide(approval.id, "approver-1", ApprovalDecisionType.APPROVE)

    assert len(decided.history) == 2
    assert decided.history[0].decision is ApprovalDecisionType.REQUEST_CHANGES
    assert decided.history[1].decision is ApprovalDecisionType.APPROVE


def test_decide_by_a_non_approver_raises() -> None:
    engine = _engine()
    approval = engine.request(
        "ws-1", "document", "doc-1", "requester", ["approver-1"], ApprovalMode.SINGLE
    )

    with pytest.raises(ValueError, match="is not an approver"):
        engine.decide(approval.id, "stranger", ApprovalDecisionType.APPROVE)


def test_decide_on_unknown_approval_raises() -> None:
    engine = _engine()

    with pytest.raises(ValueError, match="Unknown approval"):
        engine.decide("nope", "approver-1", ApprovalDecisionType.APPROVE)


def test_list_for_target_returns_matching_requests() -> None:
    engine = _engine()
    engine.request("ws-1", "document", "doc-1", "requester", ["approver-1"], ApprovalMode.SINGLE)
    engine.request("ws-1", "document", "doc-2", "requester", ["approver-1"], ApprovalMode.SINGLE)

    found = engine.list_for_target("document", "doc-1")

    assert len(found) == 1
    assert found[0].target_id == "doc-1"
