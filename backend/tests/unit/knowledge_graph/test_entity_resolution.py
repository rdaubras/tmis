from tmis.ai_governance.human_validation.engine import HumanValidationEngine
from tmis.ai_governance.human_validation.schemas import ValidationDecisionType
from tmis.ai_governance.human_validation.store import InMemoryValidationStore
from tmis.knowledge_graph.entity_resolution.engine import EntityResolutionEngine
from tmis.knowledge_graph.entity_resolution.schemas import EntityOccurrence, ResolutionStatus
from tmis.knowledge_graph.entity_resolution.store import InMemoryResolvedEntityStore
from tmis.knowledge_graph.federation.schemas import GraphOrigin

FIRM = "firm-a"


def _engine() -> EntityResolutionEngine:
    return EntityResolutionEngine(
        InMemoryResolvedEntityStore(), HumanValidationEngine(InMemoryValidationStore())
    )


def test_matching_labels_are_confirmed_without_human_validation() -> None:
    engine = _engine()
    occurrences = [
        EntityOccurrence(origin=GraphOrigin.CASE_GRAPH, node_id="actor-1", label="Jean Dupont"),
        EntityOccurrence(
            origin=GraphOrigin.DOCUMENT_KNOWLEDGE_GRAPH, node_id="entity-1", label="Jean Dupont"
        ),
    ]

    resolved = engine.resolve(FIRM, "user-1", occurrences)

    assert resolved.status is ResolutionStatus.CONFIRMED
    assert resolved.confidence == 1.0
    assert resolved.validation_request_id is None


def test_a_single_occurrence_is_trivially_confirmed() -> None:
    engine = _engine()
    occurrences = [
        EntityOccurrence(origin=GraphOrigin.CASE_GRAPH, node_id="actor-1", label="Jean Dupont")
    ]

    resolved = engine.resolve(FIRM, "user-1", occurrences)

    assert resolved.status is ResolutionStatus.CONFIRMED
    assert resolved.confidence == 1.0


def test_dissimilar_labels_are_routed_to_human_validation() -> None:
    engine = _engine()
    occurrences = [
        EntityOccurrence(origin=GraphOrigin.CASE_GRAPH, node_id="actor-1", label="Jean Dupont"),
        EntityOccurrence(
            origin=GraphOrigin.CABINET_ONTOLOGY, node_id="know-1", label="ACME Corporation"
        ),
    ]

    resolved = engine.resolve(FIRM, "user-1", occurrences, approver_ids=("approver-1",))

    assert resolved.status is ResolutionStatus.PENDING_VALIDATION
    assert resolved.confidence < 0.85
    assert resolved.validation_request_id is not None


def test_decide_approve_confirms_a_pending_resolution() -> None:
    engine = _engine()
    occurrences = [
        EntityOccurrence(origin=GraphOrigin.CASE_GRAPH, node_id="actor-1", label="Jean Dupont"),
        EntityOccurrence(
            origin=GraphOrigin.CABINET_ONTOLOGY, node_id="know-1", label="ACME Corporation"
        ),
    ]
    resolved = engine.resolve(FIRM, "user-1", occurrences, approver_ids=("approver-1",))

    confirmed = engine.decide(FIRM, resolved.id, "approver-1", ValidationDecisionType.APPROVE)

    assert confirmed.status is ResolutionStatus.CONFIRMED


def test_decide_reject_rejects_a_pending_resolution() -> None:
    engine = _engine()
    occurrences = [
        EntityOccurrence(origin=GraphOrigin.CASE_GRAPH, node_id="actor-1", label="Jean Dupont"),
        EntityOccurrence(
            origin=GraphOrigin.CABINET_ONTOLOGY, node_id="know-1", label="ACME Corporation"
        ),
    ]
    resolved = engine.resolve(FIRM, "user-1", occurrences, approver_ids=("approver-1",))

    rejected = engine.decide(FIRM, resolved.id, "approver-1", ValidationDecisionType.REJECT)

    assert rejected.status is ResolutionStatus.REJECTED


def test_decide_without_pending_validation_raises() -> None:
    engine = _engine()
    occurrences = [
        EntityOccurrence(origin=GraphOrigin.CASE_GRAPH, node_id="actor-1", label="Jean Dupont")
    ]
    resolved = engine.resolve(FIRM, "user-1", occurrences)

    try:
        engine.decide(FIRM, resolved.id, "approver-1", ValidationDecisionType.APPROVE)
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_get_and_list_for_firm() -> None:
    engine = _engine()
    occurrences = [
        EntityOccurrence(origin=GraphOrigin.CASE_GRAPH, node_id="actor-1", label="Jean Dupont")
    ]
    resolved = engine.resolve(FIRM, "user-1", occurrences)

    assert engine.get(FIRM, resolved.id) == resolved
    assert engine.get("other-firm", resolved.id) is None
    assert engine.list_for_firm(FIRM) == [resolved]
