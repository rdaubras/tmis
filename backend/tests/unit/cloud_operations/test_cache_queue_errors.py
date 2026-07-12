from tmis.cloud_operations.cache.engine import CacheObservabilityEngine
from tmis.cloud_operations.error_tracking.engine import ErrorTrackingEngine
from tmis.cloud_operations.error_tracking.schemas import ErrorSeverity
from tmis.cloud_operations.error_tracking.store import InMemoryErrorEventStore
from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory
from tmis.cloud_operations.metrics.store import InMemoryMetricEventStore
from tmis.cloud_operations.queue_monitoring.engine import QueueObservabilityEngine
from tmis.platform.metrics.registry import MetricsRegistry


def _metrics_engine() -> MetricsEngine:
    return MetricsEngine(InMemoryMetricEventStore(), MetricsRegistry())


def test_cache_observability_tracks_hit_miss_ratio_and_size() -> None:
    metrics = _metrics_engine()
    cache = CacheObservabilityEngine(metrics)
    cache.record_hit("rag-embeddings", firm_id="firm-1")
    cache.record_hit("rag-embeddings", firm_id="firm-1")
    cache.record_miss("rag-embeddings", firm_id="firm-1")
    cache.set_size("rag-embeddings", 128, firm_id="firm-1")
    cache.record_eviction("rag-embeddings", firm_id="firm-1")

    stats = cache.stats("rag-embeddings")
    assert stats.hits == 2
    assert stats.misses == 1
    assert stats.hit_ratio == 2 / 3
    assert stats.size == 128
    assert stats.evictions == 1
    assert len(metrics.history_for_category(MetricCategory.CACHE, "firm-1")) == 5


def test_queue_observability_tracks_throughput_wait_and_errors() -> None:
    metrics = _metrics_engine()
    queue = QueueObservabilityEngine(metrics)
    queue.set_size("sync-queue", 10)
    queue.record_processed("sync-queue", 50.0)
    queue.record_processed("sync-queue", 150.0)
    queue.record_error("sync-queue")
    queue.record_retry("sync-queue")

    stats = queue.stats("sync-queue")
    assert stats.processed == 2
    assert stats.average_wait_ms == 100.0
    assert stats.errors == 1
    assert stats.retries == 1


def test_error_tracking_records_and_lists_recent_errors() -> None:
    metrics = _metrics_engine()
    errors = ErrorTrackingEngine(InMemoryErrorEventStore(), metrics)
    errors.record(
        "workflow_engine", "timeout", "step timed out", severity=ErrorSeverity.HIGH, firm_id="f-1"
    )
    errors.record("ai_fabric", "provider_unavailable", "openai down")

    recent = errors.recent()
    assert len(recent) == 2
    assert recent[0].error_type == "provider_unavailable"
    assert errors.error_rate_by_source("workflow_engine") == 1
    assert len(metrics.history_for_category(MetricCategory.ERRORS)) == 2
