from tmis.cloud_operations.integration_monitoring.engine import IntegrationMonitoringEngine
from tmis.cloud_operations.workflow_monitoring.engine import WorkflowMonitoringEngine
from tmis.integration_hub.monitoring.schemas import ConnectorOperationMetric
from tmis.integration_hub.monitoring.sinks import InMemoryConnectorMetricsSink
from tmis.workflow_automation.metrics.schemas import WorkflowRunMetrics
from tmis.workflow_automation.metrics.sinks import InMemoryWorkflowMetricsSink


def test_workflow_monitoring_aggregates_runs() -> None:
    sink = InMemoryWorkflowMetricsSink()
    sink.record(WorkflowRunMetrics("wf-1", "exec-1", 100.0, 3, 1, 2, 0, 1, 0))
    sink.record(WorkflowRunMetrics("wf-1", "exec-2", 200.0, 4, 0, 1, 1, 0, 2))

    snapshot = WorkflowMonitoringEngine(sink).snapshot()
    assert snapshot.total_runs == 2
    assert snapshot.average_duration_ms == 150.0
    assert snapshot.total_errors == 1
    assert snapshot.total_retries == 1
    assert snapshot.total_validations == 3
    assert snapshot.total_cancellations == 1


def test_workflow_monitoring_snapshot_of_empty_sink_is_zeroed() -> None:
    snapshot = WorkflowMonitoringEngine(InMemoryWorkflowMetricsSink()).snapshot()
    assert snapshot.total_runs == 0
    assert snapshot.average_duration_ms == 0.0


def test_integration_monitoring_computes_per_connector_success_rate() -> None:
    sink = InMemoryConnectorMetricsSink()
    sink.record(ConnectorOperationMetric("conn-1", "firm-1", "sync", True, 50.0))
    sink.record(ConnectorOperationMetric("conn-1", "firm-1", "sync", False, 80.0, error="timeout"))

    engine = IntegrationMonitoringEngine(sink)
    snapshot = engine.snapshot("conn-1")
    assert snapshot.total_operations == 2
    assert snapshot.success_rate == 0.5
    assert snapshot.average_duration_ms == 65.0


def test_integration_monitoring_overview_covers_every_seen_connector() -> None:
    sink = InMemoryConnectorMetricsSink()
    sink.record(ConnectorOperationMetric("conn-1", "firm-1", "sync", True, 50.0))
    sink.record(ConnectorOperationMetric("conn-2", "firm-1", "sync", True, 20.0))

    overview = IntegrationMonitoringEngine(sink).overview()
    assert {s.connector_id for s in overview} == {"conn-1", "conn-2"}
