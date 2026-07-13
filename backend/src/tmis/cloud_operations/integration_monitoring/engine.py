from tmis.cloud_operations.integration_monitoring.ports import ConnectorMetricsReaderPort
from tmis.cloud_operations.integration_monitoring.schemas import IntegrationMonitoringSnapshot


class IntegrationMonitoringEngine:
    """Composes `integration_hub.monitoring` (Sprint 18) directly
    rather than a second connector-metrics ledger — that sink already
    tracks per-operation success/duration; this engine adds the
    per-connector and platform-wide aggregation."""

    def __init__(self, sink: ConnectorMetricsReaderPort) -> None:
        self._sink = sink

    def snapshot(self, connector_id: str) -> IntegrationMonitoringSnapshot:
        metrics = self._sink.for_connector(connector_id)
        average_duration = sum(m.duration_ms for m in metrics) / len(metrics) if metrics else 0.0
        return IntegrationMonitoringSnapshot(
            connector_id=connector_id,
            total_operations=len(metrics),
            success_rate=self._sink.success_rate(connector_id),
            average_duration_ms=average_duration,
        )

    def overview(self) -> list[IntegrationMonitoringSnapshot]:
        connector_ids = {m.connector_id for m in self._sink.all()}
        return [self.snapshot(connector_id) for connector_id in sorted(connector_ids)]
