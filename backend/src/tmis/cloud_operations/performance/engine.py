from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory
from tmis.cloud_operations.performance.schemas import PerformanceSnapshot


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(len(ordered) * percentile))
    return ordered[index]


class PerformanceEngine:
    """Production performance monitoring over `cloud_operations.
    metrics` history — composes it directly rather than a second
    sampling mechanism; complements (never replaces) `platform.
    performance.benchmark` for micro-benchmarking."""

    def __init__(self, metrics: MetricsEngine) -> None:
        self._metrics = metrics

    def snapshot(self, firm_id: str | None = None) -> PerformanceSnapshot:
        response_times = [
            e.value
            for e in self._metrics.history_for_category(MetricCategory.RESPONSE_TIME, firm_id)
        ]
        throughput = [
            e.value for e in self._metrics.history_for_category(MetricCategory.THROUGHPUT, firm_id)
        ]
        avg = sum(response_times) / len(response_times) if response_times else 0.0
        return PerformanceSnapshot(
            firm_id=firm_id,
            response_time_avg_ms=avg,
            response_time_p95_ms=_percentile(response_times, 0.95),
            throughput_total=sum(throughput),
            sample_count=len(response_times),
        )
