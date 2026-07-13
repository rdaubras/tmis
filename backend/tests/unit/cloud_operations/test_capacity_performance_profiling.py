from tmis.cloud_operations.capacity.engine import CapacityEngine
from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory
from tmis.cloud_operations.metrics.store import InMemoryMetricEventStore
from tmis.cloud_operations.performance.engine import PerformanceEngine
from tmis.cloud_operations.profiling.engine import ProfilingEngine
from tmis.cloud_operations.profiling.schemas import ProfilingFindingType
from tmis.cloud_operations.profiling.store import InMemoryProfilingSampleStore
from tmis.platform.metrics.registry import MetricsRegistry


def _metrics_engine() -> MetricsEngine:
    return MetricsEngine(InMemoryMetricEventStore(), MetricsRegistry())


def test_capacity_engine_projects_growth_from_two_halves_of_history() -> None:
    metrics = _metrics_engine()
    for value in (100.0, 100.0, 200.0, 200.0):
        metrics.record(MetricCategory.QUEUE_DEPTH, "sync-queue", value)

    engine = CapacityEngine(metrics)
    forecast = engine.forecast(MetricCategory.QUEUE_DEPTH, periods_ahead=1)
    assert forecast is not None
    assert forecast.projected_value > 150.0


def test_capacity_engine_returns_none_without_enough_history() -> None:
    engine = CapacityEngine(_metrics_engine())
    assert engine.forecast(MetricCategory.QUEUE_DEPTH) is None


def test_performance_engine_computes_average_and_p95() -> None:
    metrics = _metrics_engine()
    for value in (10.0, 20.0, 30.0, 1000.0):
        metrics.record(MetricCategory.RESPONSE_TIME, "api", value, firm_id="firm-1")
    metrics.record(MetricCategory.THROUGHPUT, "api-requests", 4.0, firm_id="firm-1")

    engine = PerformanceEngine(metrics)
    snapshot = engine.snapshot("firm-1")
    assert snapshot.sample_count == 4
    assert snapshot.response_time_p95_ms == 1000.0
    assert snapshot.throughput_total == 4.0


def test_profiling_engine_ranks_offenders_by_average_duration() -> None:
    engine = ProfilingEngine(InMemoryProfilingSampleStore())
    engine.record(ProfilingFindingType.SLOW_FUNCTION, "render_pdf", 120.0)
    engine.record(ProfilingFindingType.SLOW_FUNCTION, "render_pdf", 140.0)
    engine.record(ProfilingFindingType.SLOW_FUNCTION, "compute_diff", 50.0)

    top = engine.top_offenders(ProfilingFindingType.SLOW_FUNCTION)
    assert top[0].name == "render_pdf"
    assert top[0].average_duration_ms == 130.0
    assert top[0].occurrence_count == 2
    assert "render_pdf" in top[0].recommendation
