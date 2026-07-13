from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory
from tmis.cloud_operations.metrics.store import InMemoryMetricEventStore
from tmis.cloud_operations.performance.engine import PerformanceEngine
from tmis.cloud_operations.profiling.engine import ProfilingEngine
from tmis.cloud_operations.profiling.schemas import ProfilingFindingType
from tmis.cloud_operations.profiling.store import InMemoryProfilingSampleStore
from tmis.cloud_operations.workflow_monitoring.engine import WorkflowMonitoringEngine
from tmis.platform.metrics.registry import MetricsRegistry
from tmis.runtime_platform.runtime_optimizer.engine import RuntimeOptimizerEngine
from tmis.runtime_platform.runtime_optimizer.schemas import (
    OptimizationCategory,
    OptimizationSeverity,
)
from tmis.workflow_automation.metrics.sinks import InMemoryWorkflowMetricsSink


def _optimizer() -> tuple[RuntimeOptimizerEngine, MetricsEngine, ProfilingEngine]:
    metrics = MetricsEngine(InMemoryMetricEventStore(), MetricsRegistry())
    performance = PerformanceEngine(metrics)
    profiling = ProfilingEngine(InMemoryProfilingSampleStore())
    workflow_monitoring = WorkflowMonitoringEngine(InMemoryWorkflowMetricsSink())
    return (
        RuntimeOptimizerEngine(metrics, performance, profiling, workflow_monitoring),
        metrics,
        profiling,
    )


def test_analyze_returns_no_recommendations_when_all_metrics_are_healthy() -> None:
    optimizer, metrics, _ = _optimizer()
    metrics.record(MetricCategory.CPU_USAGE, "cpu", 20.0)
    metrics.record(MetricCategory.MEMORY_USAGE, "mem", 30.0)

    assert optimizer.analyze() == []


def test_analyze_flags_high_cpu_usage() -> None:
    optimizer, metrics, _ = _optimizer()
    metrics.record(MetricCategory.CPU_USAGE, "cpu", 115.0)

    recommendations = optimizer.analyze()
    cpu_recs = [r for r in recommendations if r.category is OptimizationCategory.CPU]
    assert len(cpu_recs) == 1
    assert cpu_recs[0].severity is OptimizationSeverity.HIGH


def test_analyze_flags_high_ai_call_duration() -> None:
    optimizer, metrics, _ = _optimizer()
    metrics.record(MetricCategory.AI_CALL_DURATION, "ai", 3000.0)

    recommendations = optimizer.analyze()
    assert any(r.category is OptimizationCategory.AI_CALLS for r in recommendations)


def test_analyze_includes_contention_from_blocking_operations() -> None:
    optimizer, _, profiling = _optimizer()
    profiling.record(ProfilingFindingType.BLOCKING_OPERATION, "sync_call", 500.0)

    recommendations = optimizer.analyze()
    contention = [r for r in recommendations if r.category is OptimizationCategory.CONTENTION]
    assert len(contention) == 1
    assert contention[0].metric_value == 500.0
