from tmis.ai.embeddings.hashing_provider import HashingEmbeddingProvider
from tmis.ai_governance.human_validation.engine import HumanValidationEngine
from tmis.ai_governance.human_validation.store import InMemoryValidationStore
from tmis.cabinet_knowledge.ontology.schemas import RelationType
from tmis.legal_knowledge_graph.entity_resolution.engine import EntityResolutionEngine
from tmis.legal_knowledge_graph.entity_resolution.schemas import ResolutionStatus
from tmis.legal_knowledge_graph.entity_resolution.store import InMemoryResolutionMatchStore
from tmis.legal_knowledge_graph.graph_core.engine import GraphEngine
from tmis.legal_knowledge_graph.graph_core.schemas import GraphNodeType
from tmis.legal_knowledge_graph.graph_core.store import (
    InMemoryGraphNodeStore,
    InMemoryGraphRelationStore,
)

FIRM = "firm-a"


def _graph() -> GraphEngine:
    return GraphEngine(InMemoryGraphNodeStore(), InMemoryGraphRelationStore())


def _engine(graph: GraphEngine) -> EntityResolutionEngine:
    return EntityResolutionEngine(
        InMemoryResolutionMatchStore(),
        graph,
        HashingEmbeddingProvider(),
        HumanValidationEngine(InMemoryValidationStore()),
    )


async def test_exact_normalized_name_match_scores_one() -> None:
    graph = _graph()
    engine = _engine(graph)
    a = graph.add_node(FIRM, GraphNodeType.LEGAL_ENTITY, "ko-1", "ACME Corp SARL")
    b = graph.add_node(FIRM, GraphNodeType.LEGAL_ENTITY, "ko-2", "acme corp sarl")

    score = await engine.score(FIRM, a.id, b.id)

    assert score == 1.0


async def test_propose_match_auto_confirms_exact_name_match() -> None:
    graph = _graph()
    engine = _engine(graph)
    a = graph.add_node(FIRM, GraphNodeType.LEGAL_ENTITY, "ko-1", "ACME Corp SARL")
    b = graph.add_node(FIRM, GraphNodeType.LEGAL_ENTITY, "ko-2", "ACME Corp SARL")

    match = await engine.propose_match(FIRM, a.id, b.id)

    assert match.status is ResolutionStatus.CONFIRMED
    relations = graph.relations_for(FIRM, a.id)
    assert any(r.relation_type is RelationType.SAME_AS for r in relations)


async def test_propose_match_for_dissimilar_names_stays_pending() -> None:
    graph = _graph()
    engine = _engine(graph)
    a = graph.add_node(FIRM, GraphNodeType.LEGAL_ENTITY, "ko-1", "ACME Corp SARL")
    b = graph.add_node(FIRM, GraphNodeType.LEGAL_ENTITY, "ko-2", "Société Beta SAS")

    match = await engine.propose_match(FIRM, a.id, b.id)

    assert match.status is ResolutionStatus.PENDING
    assert not any(
        r.relation_type is RelationType.SAME_AS for r in graph.relations_for(FIRM, a.id)
    )


async def test_confirm_appends_history_and_creates_same_as_relation() -> None:
    graph = _graph()
    engine = _engine(graph)
    a = graph.add_node(FIRM, GraphNodeType.LEGAL_ENTITY, "ko-1", "ACME Corp SARL")
    b = graph.add_node(FIRM, GraphNodeType.LEGAL_ENTITY, "ko-2", "ACME SARL")

    proposed = await engine.propose_match(FIRM, a.id, b.id)
    assert proposed.status is ResolutionStatus.PENDING

    confirmed = engine.confirm(FIRM, proposed.id, "Camille Lefèvre")

    assert confirmed.status is ResolutionStatus.CONFIRMED
    assert confirmed.decided_by == "Camille Lefèvre"
    history = engine.history(FIRM, proposed.id)
    assert [m.status for m in history] == [ResolutionStatus.PENDING, ResolutionStatus.CONFIRMED]
    assert any(r.relation_type is RelationType.SAME_AS for r in graph.relations_for(FIRM, a.id))


async def test_reject_appends_history_without_creating_a_relation() -> None:
    graph = _graph()
    engine = _engine(graph)
    a = graph.add_node(FIRM, GraphNodeType.LEGAL_ENTITY, "ko-1", "ACME Corp SARL")
    b = graph.add_node(FIRM, GraphNodeType.LEGAL_ENTITY, "ko-2", "Société Beta SAS")

    proposed = await engine.propose_match(FIRM, a.id, b.id)
    rejected = engine.reject(FIRM, proposed.id, "Camille Lefèvre")

    assert rejected.status is ResolutionStatus.REJECTED
    assert not any(
        r.relation_type is RelationType.SAME_AS for r in graph.relations_for(FIRM, a.id)
    )
