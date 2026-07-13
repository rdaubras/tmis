from fastapi import APIRouter, Depends, HTTPException

from tmis.ai_fabric.telemetry.schemas import FabricTelemetry
from tmis.business_platform.exports.schemas import ExportFormat
from tmis.cloud_operations.ai_monitoring.engine import AIMonitoringEngine
from tmis.cloud_operations.alerting.engine import AlertingEngine, UnknownAlertRuleError
from tmis.cloud_operations.alerting.schemas import AlertComparison, AlertSeverity
from tmis.cloud_operations.audit_pipeline.engine import AuditPipelineEngine
from tmis.cloud_operations.bootstrap import (
    ensure_business_context_health_checks_registered,
    get_ai_monitoring_engine,
    get_alerting_engine,
    get_audit_pipeline_engine,
    get_cache_observability_engine,
    get_capacity_engine,
    get_chaos_testing_engine,
    get_cost_monitoring_engine,
    get_dashboards_engine,
    get_diagnostics_engine,
    get_error_tracking_engine,
    get_incident_management_engine,
    get_integration_monitoring_engine,
    get_metrics_engine,
    get_observability_export_engine,
    get_performance_engine,
    get_profiling_engine,
    get_queue_observability_engine,
    get_retention_engine,
    get_runbooks_engine,
    get_security_monitoring_engine,
    get_sla_engine,
    get_slo_engine,
    get_tenant_monitoring_engine,
    get_tracing_engine,
    get_workflow_monitoring_engine,
)
from tmis.cloud_operations.cache.engine import CacheObservabilityEngine
from tmis.cloud_operations.capacity.engine import CapacityEngine
from tmis.cloud_operations.chaos_testing.engine import (
    ChaosTestingEngine,
    ProductionChaosTestingForbiddenError,
)
from tmis.cloud_operations.chaos_testing.schemas import ChaosScenarioType
from tmis.cloud_operations.cost_monitoring.engine import CostMonitoringEngine
from tmis.cloud_operations.dashboards.engine import DashboardsEngine
from tmis.cloud_operations.diagnostics.engine import DiagnosticsEngine
from tmis.cloud_operations.error_tracking.engine import ErrorTrackingEngine
from tmis.cloud_operations.exports.engine import ObservabilityExportEngine
from tmis.cloud_operations.incident_management.engine import (
    IncidentManagementEngine,
    UnknownIncidentError,
)
from tmis.cloud_operations.incident_management.schemas import IncidentSeverity
from tmis.cloud_operations.integration_monitoring.engine import IntegrationMonitoringEngine
from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory
from tmis.cloud_operations.performance.engine import PerformanceEngine
from tmis.cloud_operations.profiling.engine import ProfilingEngine
from tmis.cloud_operations.profiling.schemas import ProfilingFindingType
from tmis.cloud_operations.queue_monitoring.engine import QueueObservabilityEngine
from tmis.cloud_operations.retention.engine import RetentionEngine
from tmis.cloud_operations.retention.schemas import ObservabilityDataCategory
from tmis.cloud_operations.runbooks.engine import RunbooksEngine
from tmis.cloud_operations.security_monitoring.engine import SecurityMonitoringEngine
from tmis.cloud_operations.sla.engine import SLAEngine
from tmis.cloud_operations.sla.schemas import SLAMetricType
from tmis.cloud_operations.slo.engine import SLOEngine
from tmis.cloud_operations.tenant_monitoring.engine import TenantMonitoringEngine
from tmis.cloud_operations.tracing.engine import TracingEngine
from tmis.cloud_operations.workflow_monitoring.engine import WorkflowMonitoringEngine
from tmis.platform.health.schemas import HealthStatus

router = APIRouter(prefix="/cloud-operations", tags=["cloud-operations"])
"""REST surface for the sprint's "endpoints REST pour consulter
métriques, traces, incidents, alertes, dashboards, rapports de
capacité". Deliberately mounted outside `/api/v1`, unauthenticated,
next to `platform.api.routes` (see `main.py`) — the same "operational
concern, not a versioned business API" precedent already established
there for metrics/health/monitoring."""


@router.get("/metrics/{category}")
def metrics_history(
    category: MetricCategory,
    firm_id: str | None = None,
    engine: MetricsEngine = Depends(get_metrics_engine),
) -> dict[str, object]:
    history = engine.history_for_category(category, firm_id)
    return {
        "category": category.value,
        "average": engine.average(category, firm_id),
        "samples": [
            {"name": e.name, "value": e.value, "recorded_at": e.recorded_at.isoformat()}
            for e in history
        ],
    }


@router.get("/traces/{trace_id}")
def trace_detail(
    trace_id: str, engine: TracingEngine = Depends(get_tracing_engine)
) -> dict[str, object]:
    spans = engine.trace(trace_id)
    return {
        "trace_id": trace_id,
        "duration_ms": engine.trace_duration_ms(trace_id),
        "spans": [
            {
                "id": s.id,
                "parent_span_id": s.parent_span_id,
                "kind": s.kind.value,
                "name": s.name,
                "status": s.status.value,
                "started_at": s.started_at.isoformat(),
                "ended_at": s.ended_at.isoformat() if s.ended_at else None,
            }
            for s in spans
        ],
    }


@router.get("/alerts")
def alerts_history(
    firm_id: str | None = None, engine: AlertingEngine = Depends(get_alerting_engine)
) -> list[dict[str, object]]:
    return [
        {
            "id": e.id,
            "rule_name": e.rule_name,
            "severity": e.severity.value,
            "observed_value": e.observed_value,
            "threshold": e.threshold,
            "triggered_at": e.triggered_at.isoformat(),
        }
        for e in engine.history(firm_id)
    ]


@router.post("/alerts/rules")
def configure_alert_rule(
    name: str,
    category: MetricCategory,
    comparison: AlertComparison,
    threshold: float,
    severity: AlertSeverity = AlertSeverity.WARNING,
    firm_id: str | None = None,
    engine: AlertingEngine = Depends(get_alerting_engine),
) -> dict[str, str]:
    rule = engine.configure_rule(
        name, category, comparison, threshold, severity=severity, firm_id=firm_id
    )
    return {"id": rule.id, "name": rule.name}


@router.post("/alerts/evaluate")
def evaluate_alerts(
    firm_id: str | None = None, engine: AlertingEngine = Depends(get_alerting_engine)
) -> list[dict[str, object]]:
    try:
        fired = engine.evaluate_all(firm_id)
    except UnknownAlertRuleError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [{"id": e.id, "rule_name": e.rule_name, "severity": e.severity.value} for e in fired]


@router.get("/dashboards/overview")
def dashboards_overview(
    firm_id: str | None = None, engine: DashboardsEngine = Depends(get_dashboards_engine)
) -> dict[str, object]:
    overview = engine.overview(firm_id)
    return {
        "firm_id": overview.firm_id,
        "platform_status": overview.platform.system_health.status.value,
        "workflows_executed": overview.workflows.total_workflows_executed,
        "integrations_healthy": overview.integrations.healthy_connectors,
        "integrations_total": overview.integrations.total_connectors,
        "has_ai_view": overview.ai is not None,
        "has_security_view": overview.security is not None,
        "has_business_view": overview.business is not None,
        "computed_at": overview.computed_at.isoformat(),
    }


@router.get("/health")
def cloud_operations_health() -> dict[str, object]:
    engine = ensure_business_context_health_checks_registered()
    health = engine.readiness()
    status_code = 503 if health.status is HealthStatus.DOWN else 200
    return {
        "status_code": status_code,
        "status": health.status.value,
        "components": [
            {"name": c.name, "status": c.status.value, "detail": c.detail}
            for c in health.components
        ],
    }


@router.get("/sla/{service_name}/{metric_type}")
def sla_indicator(
    service_name: str, metric_type: SLAMetricType, engine: SLAEngine = Depends(get_sla_engine)
) -> dict[str, object]:
    indicator = engine.compute_indicator(service_name, metric_type)
    if indicator is None:
        raise HTTPException(status_code=404, detail="no target or samples for this metric")
    return {
        "service_name": indicator.service_name,
        "metric_type": indicator.metric_type.value,
        "target_value": indicator.target_value,
        "actual_value": indicator.actual_value,
        "met": indicator.met,
    }


@router.get("/slo/{service_name}/{metric_type}")
def slo_status(
    service_name: str, metric_type: SLAMetricType, engine: SLOEngine = Depends(get_slo_engine)
) -> dict[str, object]:
    status = engine.status(service_name, metric_type)
    if status is None:
        raise HTTPException(status_code=404, detail="no objective or samples for this metric")
    return {
        "service_name": status.service_name,
        "metric_type": status.metric_type.value,
        "objective_value": status.objective_value,
        "actual_value": status.actual_value,
        "error_budget_remaining_percent": status.error_budget_remaining_percent,
        "at_risk": status.at_risk,
    }


@router.get("/capacity/{category}")
def capacity_forecast(
    category: MetricCategory,
    firm_id: str | None = None,
    periods_ahead: int = 1,
    engine: CapacityEngine = Depends(get_capacity_engine),
) -> dict[str, object]:
    forecast = engine.forecast(category, firm_id, periods_ahead=periods_ahead)
    if forecast is None:
        raise HTTPException(status_code=404, detail="not enough history to forecast")
    return {
        "category": forecast.category.value,
        "projected_value": forecast.projected_value,
        "growth_rate_percent": forecast.growth_rate_percent,
        "periods_ahead": forecast.periods_ahead,
    }


@router.get("/performance")
def performance_snapshot(
    firm_id: str | None = None, engine: PerformanceEngine = Depends(get_performance_engine)
) -> dict[str, object]:
    snapshot = engine.snapshot(firm_id)
    return {
        "response_time_avg_ms": snapshot.response_time_avg_ms,
        "response_time_p95_ms": snapshot.response_time_p95_ms,
        "throughput_total": snapshot.throughput_total,
        "sample_count": snapshot.sample_count,
    }


@router.get("/profiling/{finding_type}")
def profiling_top_offenders(
    finding_type: ProfilingFindingType,
    limit: int = 5,
    engine: ProfilingEngine = Depends(get_profiling_engine),
) -> list[dict[str, object]]:
    return [
        {
            "name": r.name,
            "average_duration_ms": r.average_duration_ms,
            "occurrence_count": r.occurrence_count,
            "recommendation": r.recommendation,
        }
        for r in engine.top_offenders(finding_type, limit)
    ]


@router.get("/cache/{cache_name}")
def cache_stats(
    cache_name: str, engine: CacheObservabilityEngine = Depends(get_cache_observability_engine)
) -> dict[str, object]:
    stats = engine.stats(cache_name)
    return {
        "cache_name": stats.cache_name,
        "hits": stats.hits,
        "misses": stats.misses,
        "evictions": stats.evictions,
        "expirations": stats.expirations,
        "size": stats.size,
        "hit_ratio": stats.hit_ratio,
        "miss_ratio": stats.miss_ratio,
    }


@router.get("/queues/{queue_name}")
def queue_stats(
    queue_name: str, engine: QueueObservabilityEngine = Depends(get_queue_observability_engine)
) -> dict[str, object]:
    stats = engine.stats(queue_name)
    return {
        "queue_name": stats.queue_name,
        "size": stats.size,
        "processed": stats.processed,
        "errors": stats.errors,
        "retries": stats.retries,
        "average_wait_ms": stats.average_wait_ms,
    }


@router.get("/errors/recent")
def recent_errors(
    limit: int = 50, engine: ErrorTrackingEngine = Depends(get_error_tracking_engine)
) -> list[dict[str, object]]:
    return [
        {
            "id": e.id,
            "source": e.source,
            "error_type": e.error_type,
            "message": e.message,
            "severity": e.severity.value,
            "occurred_at": e.occurred_at.isoformat(),
        }
        for e in engine.recent(limit)
    ]


@router.get("/incidents")
def open_incidents(
    firm_id: str | None = None,
    engine: IncidentManagementEngine = Depends(get_incident_management_engine),
) -> list[dict[str, object]]:
    return [
        {
            "id": i.id,
            "title": i.title,
            "severity": i.severity.value,
            "status": i.status.value,
            "opened_at": i.opened_at.isoformat(),
        }
        for i in engine.open_incidents(firm_id)
    ]


@router.post("/incidents")
def open_incident(
    title: str,
    description: str,
    severity: IncidentSeverity,
    firm_id: str | None = None,
    engine: IncidentManagementEngine = Depends(get_incident_management_engine),
) -> dict[str, str]:
    incident = engine.open_incident(title, description, severity, firm_id)
    return {"id": incident.id, "status": incident.status.value}


@router.post("/incidents/{incident_id}/resolve")
def resolve_incident(
    incident_id: str,
    engine: IncidentManagementEngine = Depends(get_incident_management_engine),
) -> dict[str, str]:
    try:
        incident = engine.resolve(incident_id)
    except UnknownIncidentError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"id": incident.id, "status": incident.status.value}


@router.get("/runbooks")
def list_runbooks(engine: RunbooksEngine = Depends(get_runbooks_engine)) -> list[dict[str, object]]:
    return [{"slug": r.slug, "title": r.title, "tags": r.tags} for r in engine.list_all()]


@router.get("/runbooks/{slug}")
def runbook_detail(
    slug: str, engine: RunbooksEngine = Depends(get_runbooks_engine)
) -> dict[str, object]:
    runbook = engine.get(slug)
    if runbook is None:
        raise HTTPException(status_code=404, detail="unknown runbook")
    return {
        "slug": runbook.slug,
        "title": runbook.title,
        "trigger": runbook.trigger,
        "steps": [{"order": s.order, "instruction": s.instruction} for s in runbook.steps],
        "tags": runbook.tags,
    }


@router.get("/diagnostics")
def diagnostics_report(
    firm_id: str | None = None,
    trace_id: str | None = None,
    engine: DiagnosticsEngine = Depends(get_diagnostics_engine),
) -> dict[str, object]:
    report = engine.diagnose(firm_id, trace_id)
    return {
        "health_status": report.health.status.value,
        "response_time_avg_ms": report.response_time_avg_ms,
        "response_time_p95_ms": report.response_time_p95_ms,
        "recent_error_count": len(report.recent_errors),
        "trace_span_count": len(report.trace),
        "generated_at": report.generated_at.isoformat(),
    }


@router.post("/chaos/{scenario}")
def run_chaos_scenario(
    scenario: ChaosScenarioType,
    authorized: bool = False,
    engine: ChaosTestingEngine = Depends(get_chaos_testing_engine),
) -> dict[str, str]:
    try:
        result = engine.run_scenario(scenario, authorized=authorized)
    except ProductionChaosTestingForbiddenError as exc:
        raise HTTPException(
            status_code=403,
            detail=f"chaos scenario '{exc}' forbidden in production without authorization",
        ) from exc
    return {"scenario": result.scenario.value, "detail": result.detail}


@router.get("/audit/{firm_id}")
def audit_timeline(
    firm_id: str, engine: AuditPipelineEngine = Depends(get_audit_pipeline_engine)
) -> list[dict[str, object]]:
    return [
        {
            "source": e.source.value,
            "action": e.action,
            "summary": e.summary,
            "occurred_at": e.occurred_at.isoformat(),
        }
        for e in engine.timeline(firm_id)
    ]


@router.get("/cost/{firm_id}")
def cost_snapshot(
    firm_id: str, engine: CostMonitoringEngine = Depends(get_cost_monitoring_engine)
) -> dict[str, object]:
    snapshot = engine.snapshot(firm_id)
    return {
        "firm_id": snapshot.firm_id,
        "total_cost_usd": snapshot.total_cost_usd,
        "cost_by_model": snapshot.cost_by_model,
        "cost_by_user": snapshot.cost_by_user,
        "cache_hit_rate": snapshot.cache_hit_rate,
        "breach_count": snapshot.breach_count,
    }


def _fabric_telemetry_response(telemetry: FabricTelemetry) -> dict[str, object]:
    return {
        "fallback_rate": telemetry.fallback_rate,
        "cache_hit_rate": telemetry.cache_hit_rate,
        "models": [
            {
                "model_name": m.model_name,
                "quality_score": m.quality_score,
                "average_latency_ms": m.average_latency_ms,
                "cost_per_1k_tokens_usd": m.cost_per_1k_tokens_usd,
                "error_rate": m.error_rate,
                "total_calls": m.total_calls,
            }
            for m in telemetry.models
        ],
    }


@router.get("/ai-quality/{firm_id}")
def ai_model_snapshot(
    firm_id: str, engine: AIMonitoringEngine = Depends(get_ai_monitoring_engine)
) -> dict[str, object]:
    return _fabric_telemetry_response(engine.model_snapshot(firm_id))


@router.post("/ai-quality/{firm_id}/scan")
def ai_quality_scan(
    firm_id: str, text: str, engine: AIMonitoringEngine = Depends(get_ai_monitoring_engine)
) -> list[dict[str, object]]:
    incidents = engine.scan_and_record(text, firm_id=firm_id)
    return [{"kind": i.kind.value, "excerpt": i.excerpt, "detail": i.detail} for i in incidents]


@router.get("/ai-quality/incidents/recent")
def ai_quality_recent_incidents(
    limit: int = 50, engine: AIMonitoringEngine = Depends(get_ai_monitoring_engine)
) -> list[dict[str, object]]:
    return [
        {
            "kind": i.kind.value,
            "excerpt": i.excerpt,
            "detail": i.detail,
            "firm_id": i.firm_id,
            "detected_at": i.detected_at.isoformat(),
        }
        for i in engine.recent_incidents(limit)
    ]


@router.get("/workflow-monitoring")
def workflow_monitoring_snapshot(
    engine: WorkflowMonitoringEngine = Depends(get_workflow_monitoring_engine),
) -> dict[str, object]:
    snapshot = engine.snapshot()
    return {
        "total_runs": snapshot.total_runs,
        "average_duration_ms": snapshot.average_duration_ms,
        "total_errors": snapshot.total_errors,
        "total_retries": snapshot.total_retries,
        "total_validations": snapshot.total_validations,
        "total_cancellations": snapshot.total_cancellations,
    }


@router.get("/integration-monitoring")
def integration_monitoring_overview(
    engine: IntegrationMonitoringEngine = Depends(get_integration_monitoring_engine),
) -> list[dict[str, object]]:
    return [
        {
            "connector_id": s.connector_id,
            "total_operations": s.total_operations,
            "success_rate": s.success_rate,
            "average_duration_ms": s.average_duration_ms,
        }
        for s in engine.overview()
    ]


@router.get("/tenants/{firm_id}")
def tenant_monitoring_snapshot(
    firm_id: str, engine: TenantMonitoringEngine = Depends(get_tenant_monitoring_engine)
) -> dict[str, object]:
    try:
        snapshot = engine.snapshot(firm_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="firm has no subscription") from exc
    return {
        "firm_id": snapshot.firm_id,
        "monthly_recurring_revenue_usd": snapshot.monthly_recurring_revenue_usd,
        "total_ai_cost_usd": snapshot.total_ai_cost_usd,
        "active_modules_count": snapshot.active_modules_count,
        "open_incidents_count": snapshot.open_incidents_count,
        "quota_usage": [
            {
                "dimension": u.dimension.value,
                "used": u.used,
                "limit": u.limit,
                "percent_used": u.percent_used,
            }
            for u in snapshot.quota_usage
        ],
    }


@router.get("/security-monitoring")
def security_monitoring_overview(
    engine: SecurityMonitoringEngine = Depends(get_security_monitoring_engine),
) -> dict[str, object]:
    snapshot = engine.overview()
    return {"total_events": snapshot.total_events, "events_by_type": snapshot.events_by_type}


@router.get("/retention/{category}")
def retention_for_category(
    category: ObservabilityDataCategory, engine: RetentionEngine = Depends(get_retention_engine)
) -> dict[str, object]:
    return {"category": category.value, "retention_days": engine.retention_for(category)}


@router.post("/retention/{category}")
def set_retention_for_category(
    category: ObservabilityDataCategory,
    retention_days: int,
    engine: RetentionEngine = Depends(get_retention_engine),
) -> dict[str, object]:
    policy = engine.set_retention(category, retention_days)
    return {"category": policy.category.value, "retention_days": policy.retention_days}


@router.get("/exports/incidents")
def export_incidents(
    export_format: ExportFormat = ExportFormat.CSV,
    firm_id: str | None = None,
    incidents_engine: IncidentManagementEngine = Depends(get_incident_management_engine),
    export_engine: ObservabilityExportEngine = Depends(get_observability_export_engine),
) -> dict[str, str]:
    incidents = incidents_engine.open_incidents(firm_id)
    result = export_engine.export_incidents(incidents, export_format)
    return {
        "filename": result.filename,
        "media_type": result.media_type,
        "content": result.content.decode("utf-8"),
    }


@router.get("/exports/metrics/{category}")
def export_metrics(
    category: MetricCategory,
    export_format: ExportFormat = ExportFormat.CSV,
    firm_id: str | None = None,
    metrics_engine: MetricsEngine = Depends(get_metrics_engine),
    export_engine: ObservabilityExportEngine = Depends(get_observability_export_engine),
) -> dict[str, str]:
    events = metrics_engine.history_for_category(category, firm_id)
    result = export_engine.export_metrics(events, export_format)
    return {
        "filename": result.filename,
        "media_type": result.media_type,
        "content": result.content.decode("utf-8"),
    }
