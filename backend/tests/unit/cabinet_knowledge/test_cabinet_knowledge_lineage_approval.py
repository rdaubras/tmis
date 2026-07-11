import pytest

from tmis.cabinet_knowledge.approval.engine import ApprovalEngine, NotValidatedError
from tmis.cabinet_knowledge.approval.store import InMemoryApprovalStore
from tmis.cabinet_knowledge.governance.engine import GovernanceEngine
from tmis.cabinet_knowledge.governance.store import InMemoryGovernanceStore
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeStatus, KnowledgeType
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.lineage.engine import LineageEngine
from tmis.cabinet_knowledge.lineage.store import InMemoryLineageStore

FIRM = "firm-a"


def _space() -> KnowledgeSpace:
    return KnowledgeSpace(InMemoryKnowledgeStore())


def _governance(space: KnowledgeSpace) -> GovernanceEngine:
    return GovernanceEngine(InMemoryGovernanceStore(), space)


def test_lineage_records_origin_and_is_included_in_explanation() -> None:
    space = _space()
    obj = space.create(FIRM, KnowledgeType.NOTE, "N", {}, "avocat1")
    governance = _governance(space)
    lineage = LineageEngine(InMemoryLineageStore(), space, governance)

    lineage.record_origin(FIRM, obj.id, ("doc-42",), actor="avocat1")
    governance.transition(FIRM, obj.id, KnowledgeStatus.IN_REVIEW, actor="avocat1")

    explanation = lineage.explain(FIRM, obj.id)

    assert explanation.origin_records[0].source_refs == ("doc-42",)
    assert len(explanation.governance_events) == 1
    assert explanation.current_version == 1


def test_lineage_record_origin_rejects_unknown_object() -> None:
    space = _space()
    lineage = LineageEngine(InMemoryLineageStore(), space, _governance(space))

    with pytest.raises(KeyError):
        lineage.record_origin(FIRM, "unknown", (), actor="avocat1")


def test_approval_requires_validated_status() -> None:
    space = _space()
    obj = space.create(FIRM, KnowledgeType.NOTE, "N", {}, "avocat1")
    approval = ApprovalEngine(InMemoryApprovalStore(), space)

    with pytest.raises(NotValidatedError):
        approval.publish(FIRM, obj.id, approver="associe1")


def test_approval_publish_sets_is_published() -> None:
    space = _space()
    obj = space.create(FIRM, KnowledgeType.NOTE, "N", {}, "avocat1")
    governance = _governance(space)
    governance.transition(FIRM, obj.id, KnowledgeStatus.IN_REVIEW, actor="a")
    governance.transition(FIRM, obj.id, KnowledgeStatus.VALIDATED, actor="a")
    approval = ApprovalEngine(InMemoryApprovalStore(), space)

    published = approval.publish(FIRM, obj.id, approver="associe1")

    assert published.is_published is True
    assert approval.is_publishable(FIRM, obj.id) is True
    assert len(approval.history(FIRM, obj.id)) == 1


def test_approval_unpublish() -> None:
    space = _space()
    obj = space.create(FIRM, KnowledgeType.NOTE, "N", {}, "avocat1")
    governance = _governance(space)
    governance.transition(FIRM, obj.id, KnowledgeStatus.IN_REVIEW, actor="a")
    governance.transition(FIRM, obj.id, KnowledgeStatus.VALIDATED, actor="a")
    approval = ApprovalEngine(InMemoryApprovalStore(), space)
    approval.publish(FIRM, obj.id, approver="associe1")

    unpublished = approval.unpublish(FIRM, obj.id)

    assert unpublished.is_published is False
