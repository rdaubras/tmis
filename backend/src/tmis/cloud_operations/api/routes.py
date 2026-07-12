from fastapi import APIRouter, Depends, HTTPException

from tmis.cloud_operations.alerting.engine import AlertingEngine, UnknownAlertRuleError
from tmis.cloud_operations.alerting.schemas import AlertComparison, AlertSeverity
from tmis.cloud_operations.bootstrap import (
    ensure_business_context_health_checks_registered,
    get_alerting_engine,
    get_cache_observability_engine,
    get_capacity_engine,
    get_chaos_testing_engine,
    get_dashboards_engine,
    get_diagnostics_engine,
    get_error_tracking_engine,
    get_incident_management_engine,
    get_metrics_engine,
    get_performance_engine,
    get_profiling_engine,
    get_queue_observability_engine,
    get_runbooks_engine,
    get_sla_engine,
    get_slo_engine,
    get_tracing_engine,
)
from tmis.cloud_operations.cache.engine import CacheObservabilityEngine
from tmis.cloud_operations.capacity.engine import CapacityEngine
from tmis.cloud_operations.chaos_testing.engine import (
    ChaosTestingEngine,
    ProductionChaosTestingForbiddenError,
)
from tmis.cloud_operations.chaos_testing.schemas import ChaosScenarioType
from tmis.cloud_operations.dashboards.engine import DashboardsEngine
from tmis.cloud_operations.diagnostics.engine import DiagnosticsEngine
from tmis.cloud_operations.error_tracking.engine import ErrorTrackingEngine
from tmis.cloud_operations.incident_management.engine import (
    IncidentManagementEngine,
    UnknownIncidentError,
)
from tmis.cloud_operations.incident_management.schemas import IncidentSeverity
from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory
from tmis.cloud_operations.performance.engine import PerformanceEngine
from tmis.cloud_operations.profiling.engine import ProfilingEngine
from tmis.cloud_operations.profiling.schemas import ProfilingFindingType
from tmis.cloud_operations.queue_monitoring.engine import QueueObservabilityEngine
from tmis.cloud_operations.runbooks.engine import RunbooksEngine
from tmis.cloud_operations.sla.engine import SLAEngine
from tmis.cloud_operations.sla.schemas import SLAMetricType
from tmis.cloud_operations.slo.engine import SLOEngine
from tmis.cloud_operations.tracing.engine import TracingEngine
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
