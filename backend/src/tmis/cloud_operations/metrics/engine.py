from tmis.cloud_operations.metrics.ports import MetricEventStorePort
from tmis.cloud_operations.metrics.schemas import (
    MetricCategory,
    MetricEvent,
    MetricKind,
    new_metric_event_id,
)
from tmis.platform.metrics.registry import MetricsRegistry

_KIND_FOR_CATEGORY: dict[MetricCategory, MetricKind] = {
    MetricCategory.RESPONSE_TIME: MetricKind.HISTOGRAM,
    MetricCategory.AI_CALL_DURATION: MetricKind.HISTOGRAM,
    MetricCategory.DATABASE: MetricKind.HISTOGRAM,
    MetricCategory.MEMORY_USAGE: MetricKind.GAUGE,
    MetricCategory.CPU_USAGE: MetricKind.GAUGE,
    MetricCategory.QUEUE_DEPTH: MetricKind.GAUGE,
    MetricCategory.WORKFLOW_COUNT: MetricKind.COUNTER,
    MetricCategory.ERRORS: MetricKind.COUNTER,
    MetricCategory.THROUGHPUT: MetricKind.COUNTER,
    MetricCategory.CACHE: MetricKind.COUNTER,
    MetricCategory.COPILOT_USAGE: MetricKind.COUNTER,
    MetricCategory.AI_COST: MetricKind.GAUGE,
    MetricCategory.VALIDATION_RATE: MetricKind.GAUGE,
    MetricCategory.PACK_REUSE: MetricKind.COUNTER,
    MetricCategory.SATISFACTION: MetricKind.GAUGE,
    MetricCategory.GRAPH_SIZE: MetricKind.GAUGE,
    MetricCategory.SEARCH_LATENCY: MetricKind.HISTOGRAM,
    MetricCategory.ANSWER_QUALITY: MetricKind.GAUGE,
    MetricCategory.HUMAN_VALIDATIONS: MetricKind.COUNTER,
    MetricCategory.ENRICHMENTS: MetricKind.COUNTER,
    MetricCategory.UNRESOLVED_SEARCHES: MetricKind.COUNTER,
}


class MetricsEngine:
    """Composes `platform.metrics.MetricsRegistry` (Sprint 10) for the
    live Prometheus-exposition state rather than reimplementing
    Counter/Gauge/Histogram, and layers an append-only `MetricEvent`
    log on top so every measurement is also historisée (sprint
    requirement) — a `Counter.total()` alone cannot answer "what was
    the error rate an hour ago"."""

    def __init__(self, store: MetricEventStorePort, registry: MetricsRegistry) -> None:
        self._store = store
        self._registry = registry

    def record(
        self,
        category: MetricCategory,
        name: str,
        value: float,
        *,
        labels: dict[str, str] | None = None,
        firm_id: str | None = None,
    ) -> MetricEvent:
        labels = labels or {}
        kind = _KIND_FOR_CATEGORY[category]
        if kind is MetricKind.COUNTER:
            self._registry.counter(name, category.value).inc(value, **labels)
        elif kind is MetricKind.GAUGE:
            self._registry.gauge(name, category.value).set(value, **labels)
        else:
            self._registry.histogram(name, category.value).observe(value, **labels)
        event = MetricEvent(
            id=new_metric_event_id(),
            category=category,
            name=name,
            value=value,
            labels=labels,
            firm_id=firm_id,
        )
        self._store.save(event)
        return event

    def history_for_category(
        self, category: MetricCategory, firm_id: str | None = None
    ) -> list[MetricEvent]:
        return self._store.list_for_category(category, firm_id)

    def average(self, category: MetricCategory, firm_id: str | None = None) -> float:
        events = self.history_for_category(category, firm_id)
        if not events:
            return 0.0
        return sum(e.value for e in events) / len(events)

    def render_prometheus(self) -> str:
        return self._registry.render()
