from typing import Protocol

from tmis.integration_hub.monitoring.schemas import ConnectorOperationMetric


class ConnectorMetricsSinkPort(Protocol):
    def record(self, metric: ConnectorOperationMetric) -> None: ...
