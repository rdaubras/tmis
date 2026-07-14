from tmis.ai_governance.policy_engine.engine import PolicyEngine
from tmis.ai_governance.policy_engine.store import InMemoryGovernancePolicyStore
from tmis.cabinet_knowledge.governance.engine import GovernanceEngine
from tmis.cabinet_knowledge.governance.store import InMemoryGovernanceStore
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeStatus, KnowledgeType
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.knowledge_graph.governance.engine import KnowledgeGraphGovernance

FIRM = "firm-a"


def _governance() -> tuple[KnowledgeGraphGovernance, KnowledgeSpace, GovernanceEngine]:
    knowledge_space = KnowledgeSpace(InMemoryKnowledgeStore())
    cabinet_governance = GovernanceEngine(InMemoryGovernanceStore(), knowledge_space)
    policy_engine = PolicyEngine(InMemoryGovernancePolicyStore())
    governance = KnowledgeGraphGovernance(policy_engine, cabinet_governance)
    return governance, knowledge_space, cabinet_governance


def test_restricted_entity_visibility_blocks_wrong_role() -> None:
    governance, _, _ = _governance()
    governance.restrict_entity_visibility(FIRM, "resent-1", "PARTNER", "donnée sensible")

    evaluation = governance.evaluate_entity_visibility(FIRM, "prod-1", "resent-1", "ASSOCIATE")

    assert evaluation.allowed is False
    assert "resent-1" not in evaluation.reasons[0]  # reason references the role, not raw entity id


def test_restricted_entity_visibility_allows_matching_role() -> None:
    governance, _, _ = _governance()
    governance.restrict_entity_visibility(FIRM, "resent-1", "PARTNER", "donnée sensible")

    evaluation = governance.evaluate_entity_visibility(FIRM, "prod-1", "resent-1", "PARTNER")

    assert evaluation.allowed is True


def test_restricted_entity_visibility_does_not_affect_other_entities() -> None:
    governance, _, _ = _governance()
    governance.restrict_entity_visibility(FIRM, "resent-1", "PARTNER", "donnée sensible")

    evaluation = governance.evaluate_entity_visibility(FIRM, "prod-1", "resent-2", "ASSOCIATE")

    assert evaluation.allowed is True


def test_is_knowledge_object_validated_false_without_history() -> None:
    governance, knowledge_space, _ = _governance()
    obj = knowledge_space.create(FIRM, KnowledgeType.NOTE, "Note", {}, "author")

    assert governance.is_knowledge_object_validated(FIRM, obj.id) is False


def test_is_knowledge_object_validated_true_after_transition() -> None:
    governance, knowledge_space, cabinet_governance = _governance()
    obj = knowledge_space.create(FIRM, KnowledgeType.NOTE, "Note", {}, "author")
    cabinet_governance.transition(FIRM, obj.id, KnowledgeStatus.IN_REVIEW, "author")
    cabinet_governance.transition(FIRM, obj.id, KnowledgeStatus.VALIDATED, "reviewer")

    assert governance.is_knowledge_object_validated(FIRM, obj.id) is True
