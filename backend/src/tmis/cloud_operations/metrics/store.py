from tmis.cloud_operations.metrics.schemas import MetricCategory, MetricEvent


class InMemoryMetricEventStore:
    def __init__(self) -> None:
        self._events: list[MetricEvent] = []

    def save(self, event: MetricEvent) -> None:
        self._events.append(event)

    def list_for_category(
        self, category: MetricCategory, firm_id: str | None = None
    ) -> list[MetricEvent]:
        return [
            e
            for e in self._events
            if e.category is category and (firm_id is None or e.firm_id == firm_id)
        ]

    def list_all(self, firm_id: str | None = None) -> list[MetricEvent]:
        return [e for e in self._events if firm_id is None or e.firm_id == firm_id]
