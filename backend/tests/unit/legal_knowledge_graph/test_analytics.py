from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.store import InMemoryMetricEventStore
from tmis.legal_knowledge_graph.analytics.engine import GraphAnalyticsEngine
from tmis.platform.metrics.registry import MetricsRegistry

FIRM = "firm-a"


def _engine() -> GraphAnalyticsEngine:
    return GraphAnalyticsEngine(MetricsEngine(InMemoryMetricEventStore(), MetricsRegistry()))


def test_snapshot_of_empty_graph_is_all_zero() -> None:
    engine = _engine()

    snapshot = engine.snapshot(FIRM)

    assert snapshot.node_count == 0.0
    assert snapshot.avg_search_latency_ms == 0.0
    assert snapshot.unresolved_search_count == 0
    assert snapshot.human_validation_count == 0
    assert snapshot.enrichment_count == 0
    assert snapshot.avg_answer_quality == 0.0


def test_record_graph_size_updates_node_count() -> None:
    engine = _engine()
    engine.record_graph_size(12, 30, firm_id=FIRM)

    assert engine.snapshot(FIRM).node_count == 12.0


def test_record_search_with_results_does_not_count_as_unresolved() -> None:
    engine = _engine()
    engine.record_search(42.0, result_count=3, firm_id=FIRM)

    snapshot = engine.snapshot(FIRM)
    assert snapshot.avg_search_latency_ms == 42.0
    assert snapshot.unresolved_search_count == 0


def test_record_search_with_no_results_counts_as_unresolved() -> None:
    engine = _engine()
    engine.record_search(10.0, result_count=0, firm_id=FIRM)

    assert engine.snapshot(FIRM).unresolved_search_count == 1


def test_record_human_validation_and_enrichment_accumulate() -> None:
    engine = _engine()
    engine.record_human_validation(firm_id=FIRM)
    engine.record_human_validation(firm_id=FIRM)
    engine.record_enrichment(firm_id=FIRM)

    snapshot = engine.snapshot(FIRM)
    assert snapshot.human_validation_count == 2
    assert snapshot.enrichment_count == 1


def test_snapshot_is_scoped_per_firm() -> None:
    engine = _engine()
    engine.record_graph_size(5, 10, firm_id=FIRM)
    engine.record_graph_size(99, 200, firm_id="firm-b")

    assert engine.snapshot(FIRM).node_count == 5.0
    assert engine.snapshot("firm-b").node_count == 99.0
