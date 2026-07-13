from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory
from tmis.cloud_operations.performance.engine import PerformanceEngine
from tmis.cloud_operations.profiling.engine import ProfilingEngine
from tmis.cloud_operations.profiling.schemas import ProfilingFindingType
from tmis.cloud_operations.workflow_monitoring.engine import WorkflowMonitoringEngine
from tmis.runtime_platform.runtime_optimizer.schemas import (
    OptimizationCategory,
    OptimizationRecommendation,
    OptimizationSeverity,
)

_CPU_THRESHOLD_PERCENT = 75.0
_MEMORY_THRESHOLD_PERCENT = 80.0
_AI_CALL_DURATION_THRESHOLD_MS = 2000.0
_WORKFLOW_DURATION_THRESHOLD_MS = 5000.0
_API_LATENCY_P95_THRESHOLD_MS = 1000.0


def _severity_for_ratio(value: float, threshold: float) -> OptimizationSeverity | None:
    if value < threshold:
        return None
    if value >= threshold * 1.5:
        return OptimizationSeverity.HIGH
    if value >= threshold * 1.2:
        return OptimizationSeverity.MEDIUM
    return OptimizationSeverity.LOW


class RuntimeOptimizerEngine:
    """Composes four already-existing `cloud_operations` data sources
    — `MetricsEngine` (CPU/memory/AI-call metrics), `PerformanceEngine`
    (API latency), `ProfilingEngine` (contention — blocking
    operations), `WorkflowMonitoringEngine` (Sprint 22, workflow
    duration) — into automatic optimization recommendations. It
    introduces no new measurement mechanism of its own; every number
    it reasons about was already being collected before this sprint."""

    def __init__(
        self,
        metrics: MetricsEngine,
        performance: PerformanceEngine,
        profiling: ProfilingEngine,
        workflow_monitoring: WorkflowMonitoringEngine,
    ) -> None:
        self._metrics = metrics
        self._performance = performance
        self._profiling = profiling
        self._workflow_monitoring = workflow_monitoring

    def analyze(self, firm_id: str | None = None) -> list[OptimizationRecommendation]:
        recommendations: list[OptimizationRecommendation] = []

        cpu = self._metrics.average(MetricCategory.CPU_USAGE, firm_id)
        self._add_if_over_threshold(
            recommendations,
            OptimizationCategory.CPU,
            cpu,
            _CPU_THRESHOLD_PERCENT,
            f"CPU usage averaging {cpu:.1f}% — consider scaling out or profiling hot paths.",
        )

        memory = self._metrics.average(MetricCategory.MEMORY_USAGE, firm_id)
        self._add_if_over_threshold(
            recommendations,
            OptimizationCategory.MEMORY,
            memory,
            _MEMORY_THRESHOLD_PERCENT,
            f"Memory usage averaging {memory:.1f}% — check for leaks or increase allocation.",
        )

        ai_call_duration = self._metrics.average(MetricCategory.AI_CALL_DURATION, firm_id)
        self._add_if_over_threshold(
            recommendations,
            OptimizationCategory.AI_CALLS,
            ai_call_duration,
            _AI_CALL_DURATION_THRESHOLD_MS,
            f"AI calls averaging {ai_call_duration:.0f}ms — consider caching or batching.",
        )

        workflow_snapshot = self._workflow_monitoring.snapshot()
        self._add_if_over_threshold(
            recommendations,
            OptimizationCategory.WORKFLOW,
            workflow_snapshot.average_duration_ms,
            _WORKFLOW_DURATION_THRESHOLD_MS,
            (
                f"Workflows averaging {workflow_snapshot.average_duration_ms:.0f}ms — "
                "consider splitting long steps or increasing parallelism."
            ),
        )

        performance_snapshot = self._performance.snapshot(firm_id)
        self._add_if_over_threshold(
            recommendations,
            OptimizationCategory.API_LATENCY,
            performance_snapshot.response_time_p95_ms,
            _API_LATENCY_P95_THRESHOLD_MS,
            (
                f"API p95 latency at {performance_snapshot.response_time_p95_ms:.0f}ms — "
                "investigate slow endpoints or add caching."
            ),
        )

        blocking = self._profiling.top_offenders(ProfilingFindingType.BLOCKING_OPERATION, limit=3)
        for offender in blocking:
            recommendations.append(
                OptimizationRecommendation(
                    category=OptimizationCategory.CONTENTION,
                    severity=OptimizationSeverity.MEDIUM,
                    metric_value=offender.average_duration_ms,
                    description=offender.recommendation,
                )
            )

        return recommendations

    def _add_if_over_threshold(
        self,
        recommendations: list[OptimizationRecommendation],
        category: OptimizationCategory,
        value: float,
        threshold: float,
        description: str,
    ) -> None:
        severity = _severity_for_ratio(value, threshold)
        if severity is not None:
            recommendations.append(
                OptimizationRecommendation(
                    category=category,
                    severity=severity,
                    metric_value=value,
                    description=description,
                )
            )
