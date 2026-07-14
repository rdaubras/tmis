import pytest

from tmis.cabinet_knowledge.ontology.schemas import RelationType
from tmis.legal_knowledge_graph.graph_core.engine import GraphEngine
from tmis.legal_knowledge_graph.graph_core.schemas import GraphNodeType
from tmis.legal_knowledge_graph.graph_core.store import (
    InMemoryGraphNodeStore,
    InMemoryGraphRelationStore,
)

FIRM = "firm-a"
OTHER_FIRM = "firm-b"


def _engine() -> GraphEngine:
    return GraphEngine(InMemoryGraphNodeStore(), InMemoryGraphRelationStore())


def test_add_node_and_get_node_roundtrip() -> None:
    engine = _engine()
    node = engine.add_node(FIRM, GraphNodeType.LAW_ARTICLE, "ko-1", "Article 1134 du Code civil")

    fetched = engine.get_node(FIRM, node.id)

    assert fetched.label == "Article 1134 du Code civil"
    assert fetched.node_type is GraphNodeType.LAW_ARTICLE
    assert fetched.ref_id == "ko-1"


def test_get_unknown_node_raises_key_error() -> None:
    engine = _engine()

    with pytest.raises(KeyError):
        engine.get_node(FIRM, "does-not-exist")


def test_link_produces_explainable_relation_with_default_explanation() -> None:
    engine = _engine()
    article = engine.add_node(FIRM, GraphNodeType.LAW_ARTICLE, "ko-1", "Article 1134")
    argument = engine.add_node(FIRM, GraphNodeType.ARGUMENT, "arg-1", "Argument de bonne foi")

    relation = engine.link(FIRM, article.id, argument.id, RelationType.INFLUENCES)

    assert relation.explanation == "Article 1134 influence Argument de bonne foi"
    assert engine.explain(FIRM, relation.id) == relation.explanation


def test_link_accepts_explicit_explanation_and_confidence() -> None:
    engine = _engine()
    a = engine.add_node(FIRM, GraphNodeType.PARTY, "p-1", "ACME Corp SARL")
    b = engine.add_node(FIRM, GraphNodeType.PARTY, "p-2", "ACME SARL")

    relation = engine.link(
        FIRM, a.id, b.id, RelationType.SAME_AS, explanation="confirmé manuellement", confidence=0.9
    )

    assert relation.explanation == "confirmé manuellement"
    assert relation.confidence == 0.9


def test_neighbors_follows_relations_in_both_directions() -> None:
    engine = _engine()
    contract = engine.add_node(FIRM, GraphNodeType.CONTRACT, "ko-1", "Contrat ACME")
    article = engine.add_node(FIRM, GraphNodeType.LAW_ARTICLE, "ko-2", "Article 1134")
    jurisprudence = engine.add_node(FIRM, GraphNodeType.JURISPRUDENCE, "ko-3", "Cass. civ.")

    engine.link(FIRM, contract.id, article.id, RelationType.MENTIONS)
    engine.link(FIRM, jurisprudence.id, contract.id, RelationType.APPLIES_TO)

    neighbor_ids = {n.id for n in engine.neighbors(FIRM, contract.id)}

    assert neighbor_ids == {article.id, jurisprudence.id}


def test_list_nodes_filters_by_type_and_firm() -> None:
    engine = _engine()
    engine.add_node(FIRM, GraphNodeType.RISK, "ko-1", "Risque A")
    engine.add_node(FIRM, GraphNodeType.CONCEPT, "ko-2", "Concept A")
    engine.add_node(OTHER_FIRM, GraphNodeType.RISK, "ko-3", "Risque autre cabinet")

    risks = engine.list_nodes(FIRM, GraphNodeType.RISK)

    assert [n.ref_id for n in risks] == ["ko-1"]


def test_link_raises_key_error_when_node_belongs_to_another_firm() -> None:
    engine = _engine()
    node_a = engine.add_node(FIRM, GraphNodeType.CONCEPT, "ko-1", "A")
    node_b = engine.add_node(OTHER_FIRM, GraphNodeType.CONCEPT, "ko-2", "B")

    with pytest.raises(KeyError):
        engine.link(FIRM, node_a.id, node_b.id, RelationType.RELATED_TO)
