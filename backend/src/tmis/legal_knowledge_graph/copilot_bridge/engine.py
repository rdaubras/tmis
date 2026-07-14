from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeStatus
from tmis.legal_knowledge_graph.graph_core.engine import GraphEngine
from tmis.legal_knowledge_graph.graph_core.schemas import GraphNodeType
from tmis.legal_knowledge_graph.semantic_engine.engine import SemanticEngine


class KnowledgeGraphQueryEngine:
    """Translates a copilot's request — connaissances pertinentes,
    documents similaires, raisonnements historiques, modèles validés,
    risques identifiés (Sprint 25 Phase 7) — into graph queries.
    Never fetches anything a copilot could not already reach through
    `graph_core`/`semantic_engine`/`cabinet_knowledge.knowledge`
    directly; this class only shapes the answer for a copilot's
    `CopilotContext`."""

    def __init__(
        self, graph: GraphEngine, semantic: SemanticEngine, knowledge_space: KnowledgeSpace
    ) -> None:
        self._graph = graph
        self._semantic = semantic
        self._knowledge_space = knowledge_space

    def relevant_knowledge(self, firm_id: str, node_id: str) -> tuple[str, ...]:
        return tuple(n.label for n in self._graph.neighbors(firm_id, node_id))

    async def similar_documents(
        self, firm_id: str, node_id: str, top_k: int = 5
    ) -> tuple[str, ...]:
        matches = await self._semantic.similar_to(firm_id, node_id, top_k)
        return tuple(match.node_id for match in matches)

    def historical_reasonings(self, firm_id: str, node_id: str) -> tuple[str, ...]:
        return tuple(
            n.label
            for n in self._graph.neighbors(firm_id, node_id)
            if n.node_type is GraphNodeType.ARGUMENT
        )

    def validated_templates(self, firm_id: str) -> tuple[str, ...]:
        validated = []
        for node in self._graph.list_nodes(firm_id, GraphNodeType.DOCUMENT):
            obj = self._knowledge_space.get(firm_id, node.ref_id)
            if obj is not None and obj.status is KnowledgeStatus.VALIDATED:
                validated.append(node.label)
        return tuple(validated)

    def identified_risks(self, firm_id: str, node_id: str) -> tuple[str, ...]:
        return tuple(
            n.label
            for n in self._graph.neighbors(firm_id, node_id)
            if n.node_type is GraphNodeType.RISK
        )

    async def build_snapshot(self, firm_id: str, node_id: str) -> dict[str, tuple[str, ...]]:
        return {
            "relevant_knowledge": self.relevant_knowledge(firm_id, node_id),
            "similar_documents": await self.similar_documents(firm_id, node_id),
            "historical_reasonings": self.historical_reasonings(firm_id, node_id),
            "validated_templates": self.validated_templates(firm_id),
            "identified_risks": self.identified_risks(firm_id, node_id),
        }
