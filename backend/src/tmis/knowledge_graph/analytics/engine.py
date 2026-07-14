from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory, MetricEvent


class KnowledgeGraphAnalytics:
    """Records the three Sprint 25 measurement categories on the
    firm's existing `MetricsEngine` — never a second, parallel store
    of graph-federation metrics."""

    def __init__(self, metrics: MetricsEngine) -> None:
        self._metrics = metrics

    def record_graph_coverage(
        self, firm_id: str, resolved_occurrences: int, total_occurrences: int
    ) -> MetricEvent:
        ratio = resolved_occurrences / total_occurrences if total_occurrences else 0.0
        return self._metrics.record(
            MetricCategory.GRAPH_COVERAGE, "knowledge_graph.coverage", ratio, firm_id=firm_id
        )

    def record_entity_resolution_rate(
        self, firm_id: str, confirmed_entities: int, total_entities: int
    ) -> MetricEvent:
        ratio = confirmed_entities / total_entities if total_entities else 0.0
        return self._metrics.record(
            MetricCategory.ENTITY_RESOLUTION_RATE,
            "knowledge_graph.entity_resolution_rate",
            ratio,
            firm_id=firm_id,
        )

    def record_semantic_link_density(
        self, firm_id: str, link_count: int, object_count: int
    ) -> MetricEvent:
        density = link_count / object_count if object_count else 0.0
        return self._metrics.record(
            MetricCategory.SEMANTIC_LINK_DENSITY,
            "knowledge_graph.semantic_link_density",
            density,
            firm_id=firm_id,
        )

    def snapshot(self, firm_id: str) -> dict[str, float]:
        return {
            "graph_coverage": self._metrics.average(MetricCategory.GRAPH_COVERAGE, firm_id),
            "entity_resolution_rate": self._metrics.average(
                MetricCategory.ENTITY_RESOLUTION_RATE, firm_id
            ),
            "semantic_link_density": self._metrics.average(
                MetricCategory.SEMANTIC_LINK_DENSITY, firm_id
            ),
        }
