from tmis.integration_hub.monitoring.schemas import ConnectorOperationMetric


class InMemoryConnectorMetricsSink:
    def __init__(self) -> None:
        self._metrics: list[ConnectorOperationMetric] = []

    def record(self, metric: ConnectorOperationMetric) -> None:
        self._metrics.append(metric)

    def all(self) -> list[ConnectorOperationMetric]:
        return list(self._metrics)

    def for_connector(self, connector_id: str) -> list[ConnectorOperationMetric]:
        return [m for m in self._metrics if m.connector_id == connector_id]

    def success_rate(self, connector_id: str) -> float:
        metrics = self.for_connector(connector_id)
        if not metrics:
            return 1.0
        return sum(1 for m in metrics if m.success) / len(metrics)
