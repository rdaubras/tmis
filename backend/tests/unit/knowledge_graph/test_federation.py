from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeType
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.ontology.engine import OntologyEngine
from tmis.cabinet_knowledge.ontology.schemas import RelationType
from tmis.cabinet_knowledge.ontology.store import InMemoryRelationStore
from tmis.case_intelligence.relationships.in_memory_graph import InMemoryCaseGraph
from tmis.case_intelligence.relationships.schemas import CaseEdge, CaseNode, CaseNodeType
from tmis.document_intelligence.knowledge.in_memory_graph import InMemoryKnowledgeGraph
from tmis.document_intelligence.schemas.knowledge import KnowledgeEdge, KnowledgeNode, NodeType
from tmis.knowledge_graph.federation.engine import FederationQueryEngine
from tmis.knowledge_graph.federation.schemas import GraphOrigin

FIRM = "firm-a"


_Fixture = tuple[
    FederationQueryEngine, InMemoryCaseGraph, InMemoryKnowledgeGraph, OntologyEngine, KnowledgeSpace
]


def _engine() -> _Fixture:
    case_graph = InMemoryCaseGraph()
    knowledge_graph = InMemoryKnowledgeGraph()
    knowledge_space = KnowledgeSpace(InMemoryKnowledgeStore())
    ontology = OntologyEngine(InMemoryRelationStore(), knowledge_space)
    engine = FederationQueryEngine(case_graph, knowledge_graph, ontology)
    return engine, case_graph, knowledge_graph, ontology, knowledge_space


def test_case_neighborhood_returns_none_for_unknown_node() -> None:
    engine, *_ = _engine()
    assert engine.case_neighborhood("missing") is None


def test_case_neighborhood_projects_case_graph_nodes() -> None:
    engine, case_graph, _, _, _ = _engine()
    case_graph.add_node(CaseNode(id="actor-1", type=CaseNodeType.ACTOR, label="Jean Dupont"))
    case_graph.add_node(CaseNode(id="doc-1", type=CaseNodeType.DOCUMENT, label="bail.txt"))
    case_graph.add_edge(CaseEdge(source_id="actor-1", target_id="doc-1", relation="mentioned_in"))

    neighborhood = engine.case_neighborhood("actor-1")

    assert neighborhood is not None
    assert neighborhood.subject.origin is GraphOrigin.CASE_GRAPH
    assert neighborhood.subject.label == "Jean Dupont"
    assert [n.node_id for n in neighborhood.neighbors] == ["doc-1"]
    assert neighborhood.neighbors[0].origin is GraphOrigin.CASE_GRAPH


def test_document_neighborhood_projects_knowledge_graph_nodes() -> None:
    engine, _, knowledge_graph, _, _ = _engine()
    knowledge_graph.add_node(KnowledgeNode(id="doc-1", type=NodeType.DOCUMENT, label="bail.txt"))
    knowledge_graph.add_node(KnowledgeNode(id="entity-1", type=NodeType.ENTITY, label="ACME"))
    knowledge_graph.add_edge(
        KnowledgeEdge(source_id="doc-1", target_id="entity-1", relation="mentions")
    )

    neighborhood = engine.document_neighborhood("doc-1")

    assert neighborhood is not None
    assert neighborhood.subject.origin is GraphOrigin.DOCUMENT_KNOWLEDGE_GRAPH
    assert [n.node_id for n in neighborhood.neighbors] == ["entity-1"]


def test_cabinet_neighborhood_projects_ontology_relations() -> None:
    engine, _, _, ontology, knowledge_space = _engine()
    obj_a = knowledge_space.create(FIRM, KnowledgeType.CLAUSE, "Clause A", {}, "author")
    obj_b = knowledge_space.create(FIRM, KnowledgeType.CLAUSE, "Clause B", {}, "author")
    ontology.link(FIRM, obj_a.id, obj_b.id, RelationType.RELATED_TO)

    neighborhood = engine.cabinet_neighborhood(FIRM, obj_a.id)

    assert neighborhood.subject.origin is GraphOrigin.CABINET_ONTOLOGY
    assert [n.node_id for n in neighborhood.neighbors] == [obj_b.id]
    assert neighborhood.neighbors[0].node_type == RelationType.RELATED_TO.value


def test_cross_scope_neighborhood_gathers_one_result_per_occurrence() -> None:
    engine, case_graph, knowledge_graph, ontology, knowledge_space = _engine()
    case_graph.add_node(CaseNode(id="actor-1", type=CaseNodeType.ACTOR, label="Jean Dupont"))
    knowledge_graph.add_node(
        KnowledgeNode(id="entity-1", type=NodeType.ENTITY, label="Jean Dupont")
    )
    obj = knowledge_space.create(FIRM, KnowledgeType.NOTE, "Note", {}, "author")

    results = engine.cross_scope_neighborhood(
        FIRM,
        [
            (GraphOrigin.CASE_GRAPH, "actor-1"),
            (GraphOrigin.DOCUMENT_KNOWLEDGE_GRAPH, "entity-1"),
            (GraphOrigin.CABINET_ONTOLOGY, obj.id),
        ],
    )

    assert len(results) == 3
    assert {r.subject.origin for r in results} == {
        GraphOrigin.CASE_GRAPH,
        GraphOrigin.DOCUMENT_KNOWLEDGE_GRAPH,
        GraphOrigin.CABINET_ONTOLOGY,
    }


def test_cross_scope_neighborhood_skips_unknown_occurrences() -> None:
    engine, *_ = _engine()

    results = engine.cross_scope_neighborhood(
        FIRM,
        [(GraphOrigin.CASE_GRAPH, "missing"), (GraphOrigin.DOCUMENT_KNOWLEDGE_GRAPH, "missing")],
    )

    assert results == ()
