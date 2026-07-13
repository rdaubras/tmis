from typing import Protocol

from tmis.cloud_operations.metrics.schemas import MetricCategory, MetricEvent


class MetricEventStorePort(Protocol):
    def save(self, event: MetricEvent) -> None: ...

    def list_for_category(
        self, category: MetricCategory, firm_id: str | None = None
    ) -> list[MetricEvent]: ...

    def list_all(self, firm_id: str | None = None) -> list[MetricEvent]: ...
