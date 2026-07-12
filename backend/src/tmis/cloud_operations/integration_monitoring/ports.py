from typing import Protocol

from tmis.integration_hub.monitoring.schemas import ConnectorOperationMetric


class ConnectorMetricsReaderPort(Protocol):
    """Read-side of `integration_hub.monitoring.
    ConnectorMetricsSinkPort` — that port is write-only (`.record()`),
    but `integration_hub.monitoring.sinks.InMemoryConnectorMetricsSink`
    also exposes `.all()`/`.for_connector()`/`.success_rate()`, which
    this engine needs to aggregate."""

    def all(self) -> list[ConnectorOperationMetric]: ...

    def for_connector(self, connector_id: str) -> list[ConnectorOperationMetric]: ...

    def success_rate(self, connector_id: str) -> float: ...
