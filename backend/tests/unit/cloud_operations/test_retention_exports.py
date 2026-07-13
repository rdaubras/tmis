from datetime import UTC, datetime, timedelta

from tmis.business_platform.exports.engine import ExportEngine as BusinessExportEngine
from tmis.business_platform.exports.schemas import ExportFormat
from tmis.cloud_operations.exports.engine import ObservabilityExportEngine
from tmis.cloud_operations.incident_management.schemas import Incident, IncidentSeverity
from tmis.cloud_operations.metrics.schemas import MetricCategory, MetricEvent
from tmis.cloud_operations.retention.engine import RetentionEngine
from tmis.cloud_operations.retention.schemas import ObservabilityDataCategory
from tmis.cloud_operations.retention.store import InMemoryObservabilityRetentionPolicyStore


def test_retention_defaults_and_overrides_per_category() -> None:
    engine = RetentionEngine(InMemoryObservabilityRetentionPolicyStore())
    assert engine.retention_for(ObservabilityDataCategory.AUDIT_EVENTS) == 2_555
    assert engine.retention_for(ObservabilityDataCategory.TRACES) == 30

    engine.set_retention(ObservabilityDataCategory.METRICS, 10)
    assert engine.retention_for(ObservabilityDataCategory.METRICS) == 10


def test_retention_is_expired_respects_the_configured_window() -> None:
    engine = RetentionEngine(InMemoryObservabilityRetentionPolicyStore())
    engine.set_retention(ObservabilityDataCategory.METRICS, 10)

    old = datetime.now(UTC) - timedelta(days=11)
    fresh = datetime.now(UTC) - timedelta(days=1)
    assert engine.is_expired(ObservabilityDataCategory.METRICS, old) is True
    assert engine.is_expired(ObservabilityDataCategory.METRICS, fresh) is False


def test_export_metrics_as_csv_delegates_to_business_export_engine() -> None:
    engine = ObservabilityExportEngine(BusinessExportEngine())
    events = [
        MetricEvent(
            id="m1", category=MetricCategory.RESPONSE_TIME, name="api", value=42.0, firm_id="firm-1"
        )
    ]
    result = engine.export_metrics(events, ExportFormat.CSV)
    assert result.filename == "metrics.csv"
    assert b"api" in result.content
    assert b"42.0" in result.content


def test_export_incidents_as_json_includes_every_field() -> None:
    engine = ObservabilityExportEngine(BusinessExportEngine())
    incidents = [
        Incident(
            id="inc-1",
            title="Test",
            description="d",
            severity=IncidentSeverity.HIGH,
            firm_id="firm-1",
        )
    ]
    result = engine.export_incidents(incidents, ExportFormat.JSON)
    assert result.filename == "incidents.json"
    assert b"Test" in result.content
    assert b"high" in result.content
