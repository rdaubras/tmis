from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory
from tmis.cloud_operations.metrics.store import InMemoryMetricEventStore
from tmis.knowledge_graph.analytics.engine import KnowledgeGraphAnalytics
from tmis.platform.metrics.registry import MetricsRegistry

FIRM = "firm-a"


def _analytics() -> KnowledgeGraphAnalytics:
    metrics = MetricsEngine(InMemoryMetricEventStore(), MetricsRegistry())
    return KnowledgeGraphAnalytics(metrics)


def test_record_graph_coverage_computes_ratio() -> None:
    analytics = _analytics()
    event = analytics.record_graph_coverage(FIRM, resolved_occurrences=3, total_occurrences=4)
    assert event.category is MetricCategory.GRAPH_COVERAGE
    assert event.value == 0.75


def test_record_graph_coverage_with_zero_total_is_zero() -> None:
    analytics = _analytics()
    event = analytics.record_graph_coverage(FIRM, resolved_occurrences=0, total_occurrences=0)
    assert event.value == 0.0


def test_record_entity_resolution_rate_computes_ratio() -> None:
    analytics = _analytics()
    event = analytics.record_entity_resolution_rate(FIRM, confirmed_entities=1, total_entities=2)
    assert event.category is MetricCategory.ENTITY_RESOLUTION_RATE
    assert event.value == 0.5


def test_record_semantic_link_density_computes_ratio() -> None:
    analytics = _analytics()
    event = analytics.record_semantic_link_density(FIRM, link_count=6, object_count=3)
    assert event.category is MetricCategory.SEMANTIC_LINK_DENSITY
    assert event.value == 2.0


def test_snapshot_averages_recorded_events() -> None:
    analytics = _analytics()
    analytics.record_graph_coverage(FIRM, resolved_occurrences=1, total_occurrences=2)
    analytics.record_graph_coverage(FIRM, resolved_occurrences=1, total_occurrences=1)
    analytics.record_entity_resolution_rate(FIRM, confirmed_entities=1, total_entities=1)
    analytics.record_semantic_link_density(FIRM, link_count=2, object_count=2)

    snapshot = analytics.snapshot(FIRM)

    assert snapshot["graph_coverage"] == 0.75
    assert snapshot["entity_resolution_rate"] == 1.0
    assert snapshot["semantic_link_density"] == 1.0
