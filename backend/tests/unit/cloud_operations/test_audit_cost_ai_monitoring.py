from tmis.ai_fabric.telemetry.engine import TelemetryDashboard
from tmis.ai_governance.audit.engine import AIAuditEngine
from tmis.ai_governance.audit.store import InMemoryAIAuditStore
from tmis.ai_governance.bias_detection.engine import BiasDetectionEngine
from tmis.ai_governance.hallucination_detection.engine import HallucinationDetectionEngine
from tmis.cloud_operations.ai_monitoring.engine import AIMonitoringEngine
from tmis.cloud_operations.ai_monitoring.schemas import AIQualityIssueKind
from tmis.cloud_operations.ai_monitoring.store import InMemoryAIQualityIncidentStore
from tmis.cloud_operations.audit_pipeline.engine import AuditPipelineEngine
from tmis.cloud_operations.audit_pipeline.schemas import AuditSource
from tmis.cloud_operations.cost_monitoring.engine import CostMonitoringEngine
from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory
from tmis.cloud_operations.metrics.store import InMemoryMetricEventStore
from tmis.identity_platform.audit.engine import SecurityAuditEngine
from tmis.identity_platform.audit.store import InMemorySecurityAuditStore
from tmis.identity_platform.security_events.bus import SecurityEventBus
from tmis.platform.cost_control.engine import CostTrackerEngine
from tmis.platform.cost_control.store import InMemoryAlertThresholdStore, InMemoryCostEntryStore
from tmis.platform.metrics.registry import MetricsRegistry
from tmis.workflow_automation.audit.engine import WorkflowAuditEngine
from tmis.workflow_automation.audit.store import InMemoryWorkflowAuditStore


def test_audit_pipeline_merges_three_firm_scoped_trails_sorted_by_time() -> None:
    security_audit = SecurityAuditEngine(InMemorySecurityAuditStore(), SecurityEventBus())
    ai_audit = AIAuditEngine(InMemoryAIAuditStore())
    workflow_audit = WorkflowAuditEngine(InMemoryWorkflowAuditStore())

    ai_audit.record("firm-1", "prod-1", "user-1", "draft_generated", model_name="gpt-4o")
    workflow_audit.record("firm-1", "wf-1", "user-1", "started", execution_id="exec-1")

    pipeline = AuditPipelineEngine(security_audit, ai_audit, workflow_audit)
    timeline = pipeline.timeline("firm-1")

    assert len(timeline) == 2
    assert {e.source for e in timeline} == {AuditSource.AI_GOVERNANCE, AuditSource.WORKFLOW}
    assert timeline == sorted(timeline, key=lambda e: e.occurred_at)


def test_audit_pipeline_scopes_by_firm() -> None:
    security_audit = SecurityAuditEngine(InMemorySecurityAuditStore(), SecurityEventBus())
    ai_audit = AIAuditEngine(InMemoryAIAuditStore())
    workflow_audit = WorkflowAuditEngine(InMemoryWorkflowAuditStore())
    ai_audit.record("firm-1", "prod-1", "user-1", "draft_generated")
    ai_audit.record("firm-2", "prod-2", "user-2", "draft_generated")

    pipeline = AuditPipelineEngine(security_audit, ai_audit, workflow_audit)
    assert len(pipeline.timeline("firm-1")) == 1
    assert len(pipeline.timeline("firm-2")) == 1


def _cost_monitoring_engine() -> tuple[CostMonitoringEngine, CostTrackerEngine]:
    entries = InMemoryCostEntryStore()
    tracker = CostTrackerEngine(entries, InMemoryAlertThresholdStore())
    return CostMonitoringEngine(tracker, entries), tracker


def test_cost_monitoring_groups_by_model_and_user() -> None:
    engine, tracker = _cost_monitoring_engine()
    tracker.record("firm-1", "user-1", "openai", "gpt-4o", 1000)
    tracker.record("firm-1", "user-2", "anthropic", "claude-legal", 500)

    snapshot = engine.snapshot("firm-1")
    assert set(snapshot.cost_by_model) == {"gpt-4o", "claude-legal"}
    assert set(snapshot.cost_by_user) == {"user-1", "user-2"}
    assert snapshot.total_cost_usd == sum(snapshot.cost_by_model.values())


def test_cost_monitoring_reports_threshold_breaches() -> None:
    engine, tracker = _cost_monitoring_engine()
    tracker.record("firm-1", "user-1", "openai", "gpt-4o", 1000)
    tracker.set_alert_threshold("firm", "firm-1", max_cost_usd=0.0001)

    snapshot = engine.snapshot("firm-1")
    assert snapshot.breach_count == 1


def _unused_telemetry_dashboard_factory(firm_id: str) -> TelemetryDashboard:
    raise NotImplementedError("not exercised by this test")


def test_ai_monitoring_scans_and_historizes_hallucination_findings() -> None:
    metrics = MetricsEngine(InMemoryMetricEventStore(), MetricsRegistry())
    engine = AIMonitoringEngine(
        HallucinationDetectionEngine(),
        BiasDetectionEngine(),
        InMemoryAIQualityIncidentStore(),
        metrics,
        telemetry_dashboard_factory=_unused_telemetry_dashboard_factory,
    )

    incidents = engine.scan_and_record(
        "Une affirmation sans aucune source citée.", firm_id="firm-1"
    )
    assert len(incidents) >= 1
    assert incidents[0].kind is AIQualityIssueKind.HALLUCINATION
    assert len(engine.recent_incidents()) == len(incidents)
    assert len(metrics.history_for_category(MetricCategory.ERRORS, "firm-1")) == len(incidents)
