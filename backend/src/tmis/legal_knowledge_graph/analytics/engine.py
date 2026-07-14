from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory
from tmis.legal_knowledge_graph.analytics.schemas import GraphAnalyticsSnapshot


class GraphAnalyticsEngine:
    """Composes `cloud_operations.metrics.MetricsEngine` (Sprint 21)
    exclusively — no second metrics store, same pattern the Legal
    Copilot Framework already established in Sprint 24."""

    def __init__(self, metrics: MetricsEngine) -> None:
        self._metrics = metrics

    def record_graph_size(
        self, node_count: int, edge_count: int, firm_id: str | None = None
    ) -> None:
        self._metrics.record(
            MetricCategory.GRAPH_SIZE, "graph.node_count", node_count, firm_id=firm_id
        )
        self._metrics.record(
            MetricCategory.GRAPH_SIZE, "graph.edge_count", edge_count, firm_id=firm_id
        )

    def record_search(
        self, duration_ms: float, result_count: int, firm_id: str | None = None
    ) -> None:
        self._metrics.record(
            MetricCategory.SEARCH_LATENCY, "graph.search_latency", duration_ms, firm_id=firm_id
        )
        if result_count == 0:
            self._metrics.record(
                MetricCategory.UNRESOLVED_SEARCHES, "graph.unresolved_search", 1.0, firm_id=firm_id
            )

    def record_answer_quality(self, score: float, firm_id: str | None = None) -> None:
        self._metrics.record(
            MetricCategory.ANSWER_QUALITY, "graph.answer_quality", score, firm_id=firm_id
        )

    def record_human_validation(self, firm_id: str | None = None) -> None:
        self._metrics.record(
            MetricCategory.HUMAN_VALIDATIONS, "graph.human_validation", 1.0, firm_id=firm_id
        )

    def record_enrichment(self, firm_id: str | None = None) -> None:
        self._metrics.record(MetricCategory.ENRICHMENTS, "graph.enrichment", 1.0, firm_id=firm_id)

    def snapshot(self, firm_id: str | None = None) -> GraphAnalyticsSnapshot:
        node_size_events = [
            e.value
            for e in self._metrics.history_for_category(MetricCategory.GRAPH_SIZE, firm_id)
            if e.name == "graph.node_count"
        ]
        unresolved = self._metrics.history_for_category(MetricCategory.UNRESOLVED_SEARCHES, firm_id)
        human_validations = self._metrics.history_for_category(
            MetricCategory.HUMAN_VALIDATIONS, firm_id
        )
        enrichments = self._metrics.history_for_category(MetricCategory.ENRICHMENTS, firm_id)

        return GraphAnalyticsSnapshot(
            node_count=node_size_events[-1] if node_size_events else 0.0,
            avg_search_latency_ms=self._metrics.average(MetricCategory.SEARCH_LATENCY, firm_id),
            unresolved_search_count=len(unresolved),
            human_validation_count=len(human_validations),
            enrichment_count=len(enrichments),
            avg_answer_quality=self._metrics.average(MetricCategory.ANSWER_QUALITY, firm_id),
        )
