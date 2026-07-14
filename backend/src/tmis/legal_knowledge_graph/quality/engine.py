from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.lineage.engine import LineageEngine
from tmis.cabinet_knowledge.ontology.schemas import RelationType
from tmis.cabinet_knowledge.quality.engine import QualityEngine
from tmis.legal_knowledge_graph.graph_core.engine import GraphEngine
from tmis.legal_knowledge_graph.quality.schemas import GraphQualityBreakdown

_DUPLICATE_PENALTY = 0.8
_CONTRADICTION_PENALTY = 0.7
_MISSING_SOURCE_PENALTY = 0.9
_NO_UNDERLYING_OBJECT_SCORE = 0.5
"""A node with no `KnowledgeObject` behind it (a `CASE`/`PARTY`
pointer into another context) has no `QualityEngine` score to
inherit — treated as neutral rather than zero or perfect."""


class GraphQualityEngine:
    """The Sprint 25 Quality Engine (Phase 9): extends
    `cabinet_knowledge.quality.QualityEngine` (Sprint 12) with the
    three graph-specific signals it cannot see on its own — doublons
    (via `entity_resolution`'s `SAME_AS` relations), incohérences
    (via `RelationType.CONTRADICTS`), sources manquantes (via
    `cabinet_knowledge.lineage`) — composed into one confidence
    score, never a second quality engine."""

    def __init__(
        self,
        quality: QualityEngine,
        lineage: LineageEngine,
        graph: GraphEngine,
        knowledge_space: KnowledgeSpace,
    ) -> None:
        self._quality = quality
        self._lineage = lineage
        self._graph = graph
        self._knowledge_space = knowledge_space

    def duplicate_count(self, firm_id: str, node_id: str) -> int:
        return sum(
            1
            for r in self._graph.relations_for(firm_id, node_id)
            if r.relation_type is RelationType.SAME_AS
        )

    def contradiction_count(self, firm_id: str, node_id: str) -> int:
        return sum(
            1
            for r in self._graph.relations_for(firm_id, node_id)
            if r.relation_type is RelationType.CONTRADICTS
        )

    def evaluate(self, firm_id: str, node_id: str) -> GraphQualityBreakdown:
        node = self._graph.get_node(firm_id, node_id)
        duplicate_count = self.duplicate_count(firm_id, node_id)
        contradiction_count = self.contradiction_count(firm_id, node_id)

        obj = self._knowledge_space.get(firm_id, node.ref_id)
        base_quality = self._quality.evaluate(firm_id, obj) if obj is not None else None
        missing_sources = True
        if obj is not None:
            explanation = self._lineage.explain(firm_id, node.ref_id)
            missing_sources = len(explanation.origin_records) == 0

        confidence = (
            base_quality.overall if base_quality is not None else _NO_UNDERLYING_OBJECT_SCORE
        )
        if duplicate_count:
            confidence *= _DUPLICATE_PENALTY
        if contradiction_count:
            confidence *= _CONTRADICTION_PENALTY
        if missing_sources:
            confidence *= _MISSING_SOURCE_PENALTY

        return GraphQualityBreakdown(
            node_id=node_id,
            base_quality=base_quality,
            duplicate_count=duplicate_count,
            contradiction_count=contradiction_count,
            missing_sources=missing_sources,
            confidence=max(0.0, min(1.0, confidence)),
        )
