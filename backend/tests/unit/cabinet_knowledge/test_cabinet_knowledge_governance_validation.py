import pytest

from tmis.cabinet_knowledge.governance.engine import GovernanceEngine
from tmis.cabinet_knowledge.governance.schemas import InvalidTransitionError
from tmis.cabinet_knowledge.governance.store import InMemoryGovernanceStore
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeStatus, KnowledgeType
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.validation.engine import ValidationEngine
from tmis.cabinet_knowledge.validation.schemas import (
    ValidationDecision,
    ValidationRequestStatus,
)
from tmis.cabinet_knowledge.validation.store import InMemoryValidationStore

FIRM = "firm-a"


def _space() -> KnowledgeSpace:
    return KnowledgeSpace(InMemoryKnowledgeStore())


def _governance(space: KnowledgeSpace) -> GovernanceEngine:
    return GovernanceEngine(InMemoryGovernanceStore(), space)


def _validation(space: KnowledgeSpace, governance: GovernanceEngine) -> ValidationEngine:
    return ValidationEngine(InMemoryValidationStore(), space, governance)


def test_governance_valid_transition_is_recorded() -> None:
    space = _space()
    obj = space.create(FIRM, KnowledgeType.NOTE, "N", {}, "avocat1")
    governance = _governance(space)

    governance.transition(FIRM, obj.id, KnowledgeStatus.IN_REVIEW, actor="avocat1")

    history = governance.history(FIRM, obj.id)
    assert len(history) == 1
    assert history[0].to_status is KnowledgeStatus.IN_REVIEW


def test_governance_rejects_illegal_transition() -> None:
    space = _space()
    obj = space.create(FIRM, KnowledgeType.NOTE, "N", {}, "avocat1")
    governance = _governance(space)

    with pytest.raises(InvalidTransitionError):
        governance.transition(FIRM, obj.id, KnowledgeStatus.VALIDATED, actor="avocat1")


def test_governance_archived_is_terminal() -> None:
    space = _space()
    obj = space.create(FIRM, KnowledgeType.NOTE, "N", {}, "avocat1")
    governance = _governance(space)
    governance.transition(FIRM, obj.id, KnowledgeStatus.IN_REVIEW, actor="a")
    governance.transition(FIRM, obj.id, KnowledgeStatus.VALIDATED, actor="a")
    governance.transition(FIRM, obj.id, KnowledgeStatus.ARCHIVED, actor="a")

    with pytest.raises(InvalidTransitionError):
        governance.transition(FIRM, obj.id, KnowledgeStatus.DRAFT, actor="a")


def test_validation_submit_moves_to_in_review() -> None:
    space = _space()
    obj = space.create(FIRM, KnowledgeType.NOTE, "N", {}, "avocat1")
    governance = _governance(space)
    validation = _validation(space, governance)

    request = validation.submit_for_validation(FIRM, obj.id, requested_by="avocat1")

    assert request.status is ValidationRequestStatus.PENDING
    assert space.get(FIRM, obj.id).status is KnowledgeStatus.IN_REVIEW  # type: ignore[union-attr]


def test_validation_approve_reaches_validated_status() -> None:
    space = _space()
    obj = space.create(FIRM, KnowledgeType.NOTE, "N", {}, "avocat1")
    governance = _governance(space)
    validation = _validation(space, governance)
    request = validation.submit_for_validation(FIRM, obj.id, requested_by="avocat1")

    decided = validation.decide(FIRM, request.id, ValidationDecision.APPROVE, reviewer="associe1")

    assert decided.status is ValidationRequestStatus.APPROVED
    assert space.get(FIRM, obj.id).status is KnowledgeStatus.VALIDATED  # type: ignore[union-attr]


def test_validation_reject_returns_object_to_draft() -> None:
    space = _space()
    obj = space.create(FIRM, KnowledgeType.NOTE, "N", {}, "avocat1")
    governance = _governance(space)
    validation = _validation(space, governance)
    request = validation.submit_for_validation(FIRM, obj.id, requested_by="avocat1")

    decided = validation.decide(FIRM, request.id, ValidationDecision.REJECT, reviewer="associe1")

    assert decided.status is ValidationRequestStatus.REJECTED
    assert space.get(FIRM, obj.id).status is KnowledgeStatus.DRAFT  # type: ignore[union-attr]


def test_validation_cannot_be_created_directly_without_going_through_draft() -> None:
    """Nothing in `KnowledgeSpace.create` can start an object above
    DRAFT — the only way to reach VALIDATED is this module."""
    space = _space()
    obj = space.create(FIRM, KnowledgeType.NOTE, "N", {}, "avocat1")

    assert obj.status is KnowledgeStatus.DRAFT


def test_validation_decide_twice_raises() -> None:
    space = _space()
    obj = space.create(FIRM, KnowledgeType.NOTE, "N", {}, "avocat1")
    governance = _governance(space)
    validation = _validation(space, governance)
    request = validation.submit_for_validation(FIRM, obj.id, requested_by="avocat1")
    validation.decide(FIRM, request.id, ValidationDecision.APPROVE, reviewer="associe1")

    with pytest.raises(ValueError, match="already decided"):
        validation.decide(FIRM, request.id, ValidationDecision.APPROVE, reviewer="associe1")
