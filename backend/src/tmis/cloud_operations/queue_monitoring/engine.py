from dataclasses import dataclass, field

from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory
from tmis.cloud_operations.queue_monitoring.schemas import QueueStats


@dataclass
class _RawQueueCounters:
    size: int = 0
    processed: int = 0
    errors: int = 0
    retries: int = 0
    wait_times_ms: list[float] = field(default_factory=list)


class QueueObservabilityEngine:
    """Instrumentation wrapper layer — no existing queue implementation
    (`integration_hub.queue.InMemorySyncQueue`, `ai_team.work_queue`)
    tracks size/throughput/wait-time/error/retry statistics, confirmed
    by direct inspection. Callers report events here alongside their
    normal enqueue/dequeue logic; every event is also forwarded into
    `cloud_operations.metrics.MetricsEngine` for historization."""

    def __init__(self, metrics: MetricsEngine) -> None:
        self._metrics = metrics
        self._counters: dict[str, _RawQueueCounters] = {}

    def _counters_for(self, queue_name: str) -> _RawQueueCounters:
        return self._counters.setdefault(queue_name, _RawQueueCounters())

    def set_size(self, queue_name: str, size: int, firm_id: str | None = None) -> None:
        self._counters_for(queue_name).size = size
        self._metrics.record(
            MetricCategory.QUEUE_DEPTH, f"{queue_name}.size", float(size), firm_id=firm_id
        )

    def record_processed(self, queue_name: str, wait_ms: float, firm_id: str | None = None) -> None:
        counters = self._counters_for(queue_name)
        counters.processed += 1
        counters.wait_times_ms.append(wait_ms)
        self._metrics.record(
            MetricCategory.THROUGHPUT, f"{queue_name}.processed", 1.0, firm_id=firm_id
        )
        self._metrics.record(
            MetricCategory.RESPONSE_TIME, f"{queue_name}.wait", wait_ms, firm_id=firm_id
        )

    def record_error(self, queue_name: str, firm_id: str | None = None) -> None:
        self._counters_for(queue_name).errors += 1
        self._metrics.record(MetricCategory.ERRORS, f"{queue_name}.error", 1.0, firm_id=firm_id)

    def record_retry(self, queue_name: str, firm_id: str | None = None) -> None:
        self._counters_for(queue_name).retries += 1
        self._metrics.record(MetricCategory.ERRORS, f"{queue_name}.retry", 1.0, firm_id=firm_id)

    def stats(self, queue_name: str) -> QueueStats:
        counters = self._counters_for(queue_name)
        wait_times = counters.wait_times_ms
        average_wait = sum(wait_times) / len(wait_times) if wait_times else 0.0
        return QueueStats(
            queue_name=queue_name,
            size=counters.size,
            processed=counters.processed,
            errors=counters.errors,
            retries=counters.retries,
            average_wait_ms=average_wait,
        )
