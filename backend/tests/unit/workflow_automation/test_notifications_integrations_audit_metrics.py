import pytest

from tmis.collaboration.bootstrap import get_notification_engine
from tmis.workflow_automation.audit import InMemoryWorkflowAuditStore, WorkflowAuditEngine
from tmis.workflow_automation.integrations import (
    IntegrationRegistry,
    IntegrationResult,
    UnknownIntegrationError,
)
from tmis.workflow_automation.metrics import (
    InMemoryWorkflowMetricsSink,
    WorkflowMetricsEngine,
    WorkflowRunMetrics,
)
from tmis.workflow_automation.notifications import WorkflowNotificationAdapter


def test_notification_adapter_reuses_collaboration_notification_engine() -> None:
    adapter = WorkflowNotificationAdapter(get_notification_engine())

    notifications = adapter.notify(
        "firm-notif-test", "avocat-1", "workflow.step_completed", {"workflow": "Ouverture"}
    )

    assert len(notifications) == 1
    assert notifications[0].recipient_id == "avocat-1"


class _FakeIntegration:
    name = "calendar"

    def call(self, action_type: str, context: dict[str, str]) -> IntegrationResult:
        return IntegrationResult(success=True, detail="synced")


def test_integration_registry_register_and_get() -> None:
    registry = IntegrationRegistry()
    registry.register(_FakeIntegration())

    assert registry.list_names() == ["calendar"]
    assert registry.get("calendar").call("sync", {}).success is True


def test_integration_registry_unknown_raises() -> None:
    registry = IntegrationRegistry()

    with pytest.raises(UnknownIntegrationError):
        registry.get("unknown")


def test_workflow_audit_engine_records_and_lists() -> None:
    engine = WorkflowAuditEngine(InMemoryWorkflowAuditStore())
    engine.record("firm-1", "wf-1", "avocat-1", "workflow.activated", detail="v2 activée")
    engine.record("firm-1", "wf-2", "avocat-1", "workflow.created")

    assert len(engine.list_for_firm("firm-1")) == 2
    assert len(engine.list_for_workflow("firm-1", "wf-1")) == 1


def test_workflow_audit_engine_export_csv_includes_header_and_rows() -> None:
    engine = WorkflowAuditEngine(InMemoryWorkflowAuditStore())
    engine.record("firm-1", "wf-1", "avocat-1", "workflow.activated")

    csv_text = engine.export_csv("firm-1")

    lines = csv_text.strip().splitlines()
    assert lines[0].startswith("id,workflow_id")
    assert len(lines) == 2


def test_workflow_metrics_engine_fans_out_to_all_sinks() -> None:
    sink_a = InMemoryWorkflowMetricsSink()
    sink_b = InMemoryWorkflowMetricsSink()
    engine = WorkflowMetricsEngine([sink_a, sink_b])

    engine.record(WorkflowRunMetrics("wf-1", "exec-1", 100.0, 3, 0, 1, 0, 0, 1))

    assert len(sink_a.all()) == 1
    assert len(sink_b.all()) == 1
