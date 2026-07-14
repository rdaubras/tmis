"""Integration test: `FederationQueryEngine` composed with the three
real graph implementations (`InMemoryCaseGraph`, `InMemoryKnowledgeGraph`,
`OntologyEngine`+`InMemoryRelationStore`), each built through its own
real construction path (the document graph via `KnowledgeGraphBuilder`,
exactly as `document_intelligence` builds it end-to-end) rather than
hand-crafted fakes — proving the federation layer performs a real
cross-scope traversal, never its own storage."""

from tmis.ai.rag.ports import Chunk
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeType
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.ontology.engine import OntologyEngine
from tmis.cabinet_knowledge.ontology.schemas import RelationType
from tmis.cabinet_knowledge.ontology.store import InMemoryRelationStore
from tmis.case_intelligence.relationships.in_memory_graph import InMemoryCaseGraph
from tmis.case_intelligence.relationships.schemas import CaseEdge, CaseNode, CaseNodeType
from tmis.document_intelligence.entities.regex_extractor import RegexEntityExtractor
from tmis.document_intelligence.knowledge.builder import KnowledgeGraphBuilder
from tmis.document_intelligence.knowledge.in_memory_graph import InMemoryKnowledgeGraph
from tmis.document_intelligence.layout.heuristic_analyzer import HeuristicLayoutAnalyzer
from tmis.document_intelligence.schemas.knowledge import NodeType
from tmis.document_intelligence.timeline.builder import ChronologicalTimelineBuilder
from tmis.knowledge_graph.federation.engine import FederationQueryEngine
from tmis.knowledge_graph.federation.schemas import GraphOrigin

FIRM = "firm-a"


def _build_document_graph(text: str) -> InMemoryKnowledgeGraph:
    blocks = HeuristicLayoutAnalyzer().analyze(text)
    entities = RegexEntityExtractor().extract(text)
    events = ChronologicalTimelineBuilder().build("doc-1", text, entities)
    chunks = [Chunk(id="doc-1::0", document_id="doc-1", content=text, metadata={})]

    graph = InMemoryKnowledgeGraph()
    KnowledgeGraphBuilder().update(
        graph,
        document_id="doc-1",
        filename="bail.txt",
        layout_blocks=blocks,
        entities=entities,
        timeline_events=events,
        chunks=chunks,
    )
    return graph


def test_cross_scope_neighborhood_traverses_the_three_real_graphs() -> None:
    case_graph = InMemoryCaseGraph()
    case_graph.add_node(CaseNode(id="actor-1", type=CaseNodeType.ACTOR, label="Jean Dupont"))
    case_graph.add_node(CaseNode(id="doc-ref-1", type=CaseNodeType.DOCUMENT, label="bail.txt"))
    case_graph.add_edge(
        CaseEdge(source_id="actor-1", target_id="doc-ref-1", relation="mentioned_in")
    )

    document_graph = _build_document_graph("Signé le 12 janvier 2019 par Maître Jean Dupont.")

    knowledge_space = KnowledgeSpace(InMemoryKnowledgeStore())
    ontology = OntologyEngine(InMemoryRelationStore(), knowledge_space)
    playbook = knowledge_space.create(
        FIRM, KnowledgeType.PLAYBOOK, "Playbook bail commercial", {}, "author"
    )
    note = knowledge_space.create(FIRM, KnowledgeType.NOTE, "Note Jean Dupont", {}, "author")
    ontology.link(FIRM, playbook.id, note.id, RelationType.RELATED_TO)

    federation = FederationQueryEngine(case_graph, document_graph, ontology)

    entity_node_id = next(
        n.id for n in document_graph.get_neighbors("doc-1") if n.type is NodeType.ENTITY
    )

    results = federation.cross_scope_neighborhood(
        FIRM,
        [
            (GraphOrigin.CASE_GRAPH, "actor-1"),
            (GraphOrigin.DOCUMENT_KNOWLEDGE_GRAPH, entity_node_id),
            (GraphOrigin.CABINET_ONTOLOGY, playbook.id),
        ],
    )

    assert len(results) == 3

    case_result = next(r for r in results if r.subject.origin is GraphOrigin.CASE_GRAPH)
    assert case_result.subject.label == "Jean Dupont"
    assert [n.node_id for n in case_result.neighbors] == ["doc-ref-1"]

    document_result = next(
        r for r in results if r.subject.origin is GraphOrigin.DOCUMENT_KNOWLEDGE_GRAPH
    )
    assert document_result.subject.node_type == NodeType.ENTITY.value

    cabinet_result = next(r for r in results if r.subject.origin is GraphOrigin.CABINET_ONTOLOGY)
    assert [n.node_id for n in cabinet_result.neighbors] == [note.id]
