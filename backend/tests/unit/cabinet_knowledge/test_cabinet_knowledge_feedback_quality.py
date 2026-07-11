import pytest

from tmis.cabinet_knowledge.feedback.engine import FeedbackEngine
from tmis.cabinet_knowledge.feedback.schemas import FeedbackAction
from tmis.cabinet_knowledge.feedback.store import InMemoryFeedbackStore
from tmis.cabinet_knowledge.governance.engine import GovernanceEngine
from tmis.cabinet_knowledge.governance.store import InMemoryGovernanceStore
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeStatus, KnowledgeType
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.quality.engine import QualityEngine
from tmis.cabinet_knowledge.validation.engine import ValidationEngine
from tmis.cabinet_knowledge.validation.schemas import ValidationRequestStatus
from tmis.cabinet_knowledge.validation.store import InMemoryValidationStore

FIRM = "firm-a"


def _space() -> KnowledgeSpace:
    return KnowledgeSpace(InMemoryKnowledgeStore())


def _validation(space: KnowledgeSpace) -> ValidationEngine:
    governance = GovernanceEngine(InMemoryGovernanceStore(), space)
    return ValidationEngine(InMemoryValidationStore(), space, governance)


def _feedback(space: KnowledgeSpace, validation: ValidationEngine) -> FeedbackEngine:
    return FeedbackEngine(InMemoryFeedbackStore(), space, validation)


def test_feedback_submit_never_mutates_the_object() -> None:
    space = _space()
    obj = space.create(FIRM, KnowledgeType.NOTE, "N", {"text": "v1"}, "avocat1")
    validation = _validation(space)
    feedback = _feedback(space, validation)

    feedback.submit(FIRM, obj.id, FeedbackAction.MODIFY, author="avocat2", comment="à revoir")

    unchanged = space.get(FIRM, obj.id)
    assert unchanged is not None
    assert unchanged.content == {"text": "v1"}
    assert unchanged.version == 1


def test_feedback_acceptance_rate_defaults_to_one_with_no_history() -> None:
    space = _space()
    obj = space.create(FIRM, KnowledgeType.NOTE, "N", {}, "avocat1")
    feedback = _feedback(space, _validation(space))

    assert feedback.acceptance_rate(FIRM, obj.id) == 1.0


def test_feedback_acceptance_rate_computed_from_history() -> None:
    space = _space()
    obj = space.create(FIRM, KnowledgeType.NOTE, "N", {}, "avocat1")
    feedback = _feedback(space, _validation(space))
    feedback.submit(FIRM, obj.id, FeedbackAction.ACCEPT, author="a")
    feedback.submit(FIRM, obj.id, FeedbackAction.ACCEPT, author="b")
    feedback.submit(FIRM, obj.id, FeedbackAction.REJECT, author="c")

    assert feedback.acceptance_rate(FIRM, obj.id) == pytest.approx(2 / 3)


def test_apply_feedback_as_revision_routes_back_through_validation() -> None:
    space = _space()
    obj = space.create(FIRM, KnowledgeType.NOTE, "N", {"text": "v1"}, "avocat1")
    validation = _validation(space)
    feedback = _feedback(space, validation)
    fb = feedback.submit(FIRM, obj.id, FeedbackAction.MODIFY, author="avocat2")

    request = feedback.apply_feedback_as_revision(
        FIRM, fb.id, {"text": "v2"}, reviewer="associe1"
    )

    assert request.status is ValidationRequestStatus.PENDING
    updated = space.get(FIRM, obj.id)
    assert updated is not None
    assert updated.content == {"text": "v2"}
    assert updated.version == 2
    assert updated.status is KnowledgeStatus.IN_REVIEW


def test_apply_feedback_as_revision_rejects_non_modify_feedback() -> None:
    space = _space()
    obj = space.create(FIRM, KnowledgeType.NOTE, "N", {}, "avocat1")
    validation = _validation(space)
    feedback = _feedback(space, validation)
    fb = feedback.submit(FIRM, obj.id, FeedbackAction.ACCEPT, author="avocat2")

    with pytest.raises(ValueError, match="MODIFY"):
        feedback.apply_feedback_as_revision(FIRM, fb.id, {}, reviewer="associe1")


def test_quality_evaluate_and_store_persists_score() -> None:
    space = _space()
    obj = space.create(
        FIRM, KnowledgeType.NOTE, "N", {"text": "..."}, "avocat1", tags=frozenset({"rgpd"})
    )
    validation = _validation(space)
    feedback = _feedback(space, validation)
    quality = QualityEngine(space, feedback)

    breakdown = quality.evaluate_and_store(FIRM, obj.id)

    assert 0.0 <= breakdown.overall <= 1.0
    reloaded = space.get(FIRM, obj.id)
    assert reloaded is not None
    assert reloaded.quality_score == breakdown.overall


def test_quality_validated_object_scores_higher_human_validation() -> None:
    space = _space()
    obj = space.create(FIRM, KnowledgeType.NOTE, "N", {"text": "..."}, "avocat1")
    governance = GovernanceEngine(InMemoryGovernanceStore(), space)
    governance.transition(FIRM, obj.id, KnowledgeStatus.IN_REVIEW, actor="a")
    governance.transition(FIRM, obj.id, KnowledgeStatus.VALIDATED, actor="a")
    validation = _validation(space)
    quality = QualityEngine(space, _feedback(space, validation))
    reloaded = space.get(FIRM, obj.id)
    assert reloaded is not None

    breakdown = quality.evaluate(FIRM, reloaded)

    assert breakdown.human_validation == 1.0
