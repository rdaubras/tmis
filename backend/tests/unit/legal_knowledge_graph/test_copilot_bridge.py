from tmis.ai.embeddings.hashing_provider import HashingEmbeddingProvider
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeStatus, KnowledgeType
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.ontology.schemas import RelationType
from tmis.document_intelligence.classification.keyword_classifier import KeywordClassifier
from tmis.legal_copilot_framework.context_engine.schemas import CopilotContext
from tmis.legal_knowledge_graph.copilot_bridge.bridge import attach_graph_context
from tmis.legal_knowledge_graph.copilot_bridge.engine import KnowledgeGraphQueryEngine
from tmis.legal_knowledge_graph.graph_core.engine import GraphEngine
from tmis.legal_knowledge_graph.graph_core.schemas import GraphNodeType
from tmis.legal_knowledge_graph.graph_core.store import (
    InMemoryGraphNodeStore,
    InMemoryGraphRelationStore,
)
from tmis.legal_knowledge_graph.semantic_engine.engine import SemanticEngine

FIRM = "firm-a"
AUTHOR = "Julien Moreau"


_QueryEngineDeps = tuple[KnowledgeGraphQueryEngine, GraphEngine, KnowledgeSpace, SemanticEngine]


def _query_engine() -> _QueryEngineDeps:
    knowledge_space = KnowledgeSpace(InMemoryKnowledgeStore())
    graph = GraphEngine(InMemoryGraphNodeStore(), InMemoryGraphRelationStore())
    semantic = SemanticEngine(HashingEmbeddingProvider(), KeywordClassifier())
    return (
        KnowledgeGraphQueryEngine(graph, semantic, knowledge_space),
        graph,
        knowledge_space,
        semantic,
    )


def _empty_context() -> CopilotContext:
    return CopilotContext(
        firm_id=FIRM,
        user_id="associate-1",
        case_id=None,
        user_context={},
        firm_context={},
        case_context={},
        pieces=(),
        relevant_knowledge_ids=(),
        security_policies=(),
        writing_preferences={},
    )


def test_relevant_knowledge_returns_neighbor_labels() -> None:
    engine, graph, _, _ = _query_engine()
    contract = graph.add_node(FIRM, GraphNodeType.CONTRACT, "ko-1", "Contrat ACME")
    article = graph.add_node(FIRM, GraphNodeType.LAW_ARTICLE, "ko-2", "Article 1134")
    graph.link(FIRM, contract.id, article.id, RelationType.MENTIONS)

    assert engine.relevant_knowledge(FIRM, contract.id) == ("Article 1134",)


def test_identified_risks_filters_by_risk_node_type() -> None:
    engine, graph, _, _ = _query_engine()
    contract = graph.add_node(FIRM, GraphNodeType.CONTRACT, "ko-1", "Contrat ACME")
    risk = graph.add_node(FIRM, GraphNodeType.RISK, "ko-2", "Risque de résiliation")
    article = graph.add_node(FIRM, GraphNodeType.LAW_ARTICLE, "ko-3", "Article 1134")
    graph.link(FIRM, contract.id, risk.id, RelationType.RELATED_TO)
    graph.link(FIRM, contract.id, article.id, RelationType.MENTIONS)

    assert engine.identified_risks(FIRM, contract.id) == ("Risque de résiliation",)


def test_validated_templates_only_returns_validated_documents() -> None:
    engine, graph, knowledge_space, _ = _query_engine()
    validated_obj = knowledge_space.create(
        FIRM, KnowledgeType.TEMPLATE, "Modèle validé", {}, AUTHOR
    )
    validated_obj.status = KnowledgeStatus.VALIDATED
    draft_obj = knowledge_space.create(
        FIRM, KnowledgeType.TEMPLATE, "Modèle brouillon", {}, AUTHOR
    )
    graph.add_node(FIRM, GraphNodeType.DOCUMENT, validated_obj.id, "Modèle validé")
    graph.add_node(FIRM, GraphNodeType.DOCUMENT, draft_obj.id, "Modèle brouillon")

    assert engine.validated_templates(FIRM) == ("Modèle validé",)


async def test_build_snapshot_aggregates_all_five_dimensions() -> None:
    engine, graph, _, semantic = _query_engine()
    contract = graph.add_node(FIRM, GraphNodeType.CONTRACT, "ko-1", "Contrat ACME")
    argument = graph.add_node(FIRM, GraphNodeType.ARGUMENT, "arg-1", "Argument de bonne foi")
    graph.link(FIRM, contract.id, argument.id, RelationType.RELATED_TO)
    await semantic.index_node(FIRM, contract.id, "Contrat ACME")

    snapshot = await engine.build_snapshot(FIRM, contract.id)

    assert set(snapshot.keys()) == {
        "relevant_knowledge",
        "similar_documents",
        "historical_reasonings",
        "validated_templates",
        "identified_risks",
    }
    assert snapshot["historical_reasonings"] == ("Argument de bonne foi",)


async def test_attach_graph_context_is_pure_and_never_mutates_the_input() -> None:
    engine, graph, _, semantic = _query_engine()
    contract = graph.add_node(FIRM, GraphNodeType.CONTRACT, "ko-1", "Contrat ACME")
    await semantic.index_node(FIRM, contract.id, "Contrat ACME")
    context = _empty_context()

    snapshot = await engine.build_snapshot(FIRM, contract.id)
    enriched = attach_graph_context(context, snapshot)

    assert context.graph_context == {}
    assert enriched.graph_context == snapshot
    assert enriched.firm_id == context.firm_id
