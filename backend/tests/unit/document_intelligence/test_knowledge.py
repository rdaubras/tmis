from tmis.ai.rag.ports import Chunk
from tmis.document_intelligence.entities.regex_extractor import RegexEntityExtractor
from tmis.document_intelligence.knowledge.builder import KnowledgeGraphBuilder
from tmis.document_intelligence.knowledge.in_memory_graph import InMemoryKnowledgeGraph
from tmis.document_intelligence.layout.heuristic_analyzer import HeuristicLayoutAnalyzer
from tmis.document_intelligence.schemas.knowledge import KnowledgeEdge, KnowledgeNode, NodeType
from tmis.document_intelligence.timeline.builder import ChronologicalTimelineBuilder


class TestInMemoryKnowledgeGraph:
    def test_add_and_get_node(self) -> None:
        graph = InMemoryKnowledgeGraph()
        node = KnowledgeNode(id="doc-1", type=NodeType.DOCUMENT, label="bail.txt")
        graph.add_node(node)
        assert graph.get_node("doc-1") == node

    def test_get_unknown_node_returns_none(self) -> None:
        assert InMemoryKnowledgeGraph().get_node("missing") is None

    def test_get_neighbors_follows_edges(self) -> None:
        graph = InMemoryKnowledgeGraph()
        graph.add_node(KnowledgeNode(id="doc-1", type=NodeType.DOCUMENT, label="bail.txt"))
        graph.add_node(KnowledgeNode(id="entity-1", type=NodeType.ENTITY, label="ACME"))
        graph.add_edge(KnowledgeEdge(source_id="doc-1", target_id="entity-1", relation="mentions"))

        neighbors = graph.get_neighbors("doc-1")

        assert neighbors == [KnowledgeNode(id="entity-1", type=NodeType.ENTITY, label="ACME")]

    def test_node_and_edge_counts(self) -> None:
        graph = InMemoryKnowledgeGraph()
        graph.add_node(KnowledgeNode(id="a", type=NodeType.DOCUMENT, label="a"))
        graph.add_node(KnowledgeNode(id="b", type=NodeType.ENTITY, label="b"))
        graph.add_edge(KnowledgeEdge(source_id="a", target_id="b", relation="mentions"))

        assert graph.node_count == 2
        assert graph.edge_count == 1


class TestKnowledgeGraphBuilder:
    def _build(self, text: str) -> InMemoryKnowledgeGraph:
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

    def test_creates_a_document_node(self) -> None:
        graph = self._build("CONTRAT\n\nSigné le 12 janvier 2019.")
        node = graph.get_node("doc-1")
        assert node is not None
        assert node.type == NodeType.DOCUMENT
        assert node.label == "bail.txt"

    def test_creates_section_nodes_for_titles(self) -> None:
        graph = self._build("CONTRAT DE BAIL\n\nCeci est le corps du contrat.")
        neighbor_types = [n.type for n in graph.get_neighbors("doc-1")]
        assert NodeType.SECTION in neighbor_types

    def test_creates_entity_and_event_nodes(self) -> None:
        graph = self._build("Signé le 12 janvier 2019 par Maître Jean Dupont.")
        neighbor_types = [n.type for n in graph.get_neighbors("doc-1")]
        assert NodeType.DATE in neighbor_types
        assert NodeType.EVENT in neighbor_types
        assert NodeType.ENTITY in neighbor_types

    def test_creates_chunk_nodes(self) -> None:
        graph = self._build("Un texte quelconque.")
        neighbor_types = [n.type for n in graph.get_neighbors("doc-1")]
        assert NodeType.CHUNK in neighbor_types
