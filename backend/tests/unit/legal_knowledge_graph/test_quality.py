import pytest

from tmis.cabinet_knowledge.feedback.engine import FeedbackEngine
from tmis.cabinet_knowledge.feedback.store import InMemoryFeedbackStore
from tmis.cabinet_knowledge.governance.engine import GovernanceEngine
from tmis.cabinet_knowledge.governance.store import InMemoryGovernanceStore
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeType
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.lineage.engine import LineageEngine
from tmis.cabinet_knowledge.lineage.store import InMemoryLineageStore
from tmis.cabinet_knowledge.ontology.schemas import RelationType
from tmis.cabinet_knowledge.quality.engine import QualityEngine
from tmis.cabinet_knowledge.validation.engine import ValidationEngine
from tmis.cabinet_knowledge.validation.store import InMemoryValidationStore
from tmis.legal_knowledge_graph.graph_core.engine import GraphEngine
from tmis.legal_knowledge_graph.graph_core.schemas import GraphNodeType
from tmis.legal_knowledge_graph.graph_core.store import (
    InMemoryGraphNodeStore,
    InMemoryGraphRelationStore,
)
from tmis.legal_knowledge_graph.quality.engine import GraphQualityEngine

FIRM = "firm-a"
AUTHOR = "Julien Moreau"


def _engine() -> tuple[GraphQualityEngine, GraphEngine, KnowledgeSpace, LineageEngine]:
    knowledge_space = KnowledgeSpace(InMemoryKnowledgeStore())
    governance = GovernanceEngine(InMemoryGovernanceStore(), knowledge_space)
    validation = ValidationEngine(InMemoryValidationStore(), knowledge_space, governance)
    feedback = FeedbackEngine(InMemoryFeedbackStore(), knowledge_space, validation)
    quality = QualityEngine(knowledge_space, feedback)
    lineage = LineageEngine(InMemoryLineageStore(), knowledge_space, governance)
    graph = GraphEngine(InMemoryGraphNodeStore(), InMemoryGraphRelationStore())
    return (
        GraphQualityEngine(quality, lineage, graph, knowledge_space),
        graph,
        knowledge_space,
        lineage,
    )


def test_node_without_underlying_knowledge_object_gets_neutral_confidence() -> None:
    engine, graph, _, _ = _engine()
    node = graph.add_node(FIRM, GraphNodeType.CASE, "case-1", "Dossier D-2026-042")

    breakdown = engine.evaluate(FIRM, node.id)

    assert breakdown.base_quality is None
    assert breakdown.missing_sources is True
    assert breakdown.confidence == pytest.approx(0.5 * 0.9)


def test_node_with_lineage_has_no_missing_sources_penalty() -> None:
    engine, graph, knowledge_space, lineage = _engine()
    obj = knowledge_space.create(FIRM, KnowledgeType.CONTRACT, "Contrat", {}, AUTHOR)
    lineage.record_origin(FIRM, obj.id, ("source-doc-1",), AUTHOR)
    node = graph.add_node(FIRM, GraphNodeType.CONTRACT, obj.id, "Contrat")

    breakdown = engine.evaluate(FIRM, node.id)

    assert breakdown.missing_sources is False


def test_duplicate_relations_apply_a_penalty() -> None:
    engine, graph, knowledge_space, _ = _engine()
    obj = knowledge_space.create(FIRM, KnowledgeType.CONTRACT, "Contrat", {}, AUTHOR)
    node = graph.add_node(FIRM, GraphNodeType.CONTRACT, obj.id, "Contrat")
    duplicate = graph.add_node(FIRM, GraphNodeType.CONTRACT, "manual::dup", "Contrat (doublon)")
    graph.link(FIRM, node.id, duplicate.id, RelationType.SAME_AS)

    breakdown = engine.evaluate(FIRM, node.id)

    assert breakdown.duplicate_count == 1
    assert breakdown.confidence < 0.5


def test_contradiction_relations_apply_a_penalty() -> None:
    engine, graph, knowledge_space, _ = _engine()
    obj = knowledge_space.create(FIRM, KnowledgeType.CONTRACT, "Contrat", {}, AUTHOR)
    node = graph.add_node(FIRM, GraphNodeType.CONTRACT, obj.id, "Contrat")
    other = graph.add_node(FIRM, GraphNodeType.CONTRACT, "manual::other", "Autre contrat")
    graph.link(FIRM, node.id, other.id, RelationType.CONTRADICTS)

    breakdown = engine.evaluate(FIRM, node.id)

    assert breakdown.contradiction_count == 1
