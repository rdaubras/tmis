from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse

from tmis.platform.health.bootstrap import get_health_check_engine
from tmis.platform.health.engine import HealthCheckEngine
from tmis.platform.health.schemas import HealthStatus, SystemHealth
from tmis.platform.metrics.bootstrap import get_metrics_registry
from tmis.platform.monitoring.bootstrap import get_monitoring_engine
from tmis.platform.monitoring.engine import MonitoringEngine

router = APIRouter(prefix="/platform", tags=["platform"])


@router.get("/metrics")
def metrics() -> Response:
    """Prometheus text-exposition-format metrics (see
    docs/49-guide-supervision.md — Métriques). Deliberately outside
    `/api/v1` — metrics/health endpoints are an operational concern,
    not a versioned business API. Still requires a token, though: unlike
    `/health/live` and `/health/ready`, this is not in
    `auth_guard.PUBLIC_PATHS` (ADR-SEC-03, docs/07-strategie-securite.md
    — internal metrics are not broadcast without a token by default; an
    unauthenticated Prometheus scrape target would be an explicit,
    justified allowlist entry backed by a NetworkPolicy, not a silent
    addition)."""
    registry = get_metrics_registry()
    return Response(content=registry.render(), media_type="text/plain; version=0.0.4")


@router.get("/health/live")
def health_live(engine: HealthCheckEngine = Depends(get_health_check_engine)) -> Response:
    """Kubernetes liveness probe target: never checks a dependency,
    only "is this process able to respond at all" (see
    docs/49-guide-supervision.md — Health Checks)."""
    health = engine.liveness()
    return Response(status_code=200, content=health.status.value)


@router.get("/health/ready")
def health_ready(engine: HealthCheckEngine = Depends(get_health_check_engine)) -> JSONResponse:
    """Kubernetes readiness probe target: runs every registered
    dependency check and returns 200 only when nothing is `DOWN`
    (`DEGRADED` still returns 200 — degraded but serving traffic)."""
    health: SystemHealth = engine.readiness()
    status_code = 503 if health.status is HealthStatus.DOWN else 200
    body = {
        "status": health.status.value,
        "components": [
            {
                "name": c.name,
                "status": c.status.value,
                "detail": c.detail,
                "latency_ms": c.latency_ms,
            }
            for c in health.components
        ],
    }
    return JSONResponse(content=body, status_code=status_code)


@router.get("/monitoring")
def monitoring_dashboard(
    engine: MonitoringEngine = Depends(get_monitoring_engine),
) -> dict[str, object]:
    """The curated supervision dashboard (see
    docs/49-guide-supervision.md — Tableaux de bord de supervision)."""
    snapshot = engine.snapshot()
    return {
        "status": snapshot.system_health.status.value,
        "total_requests": snapshot.total_requests,
        "ai_cost_usd_total": snapshot.ai_cost_usd_total,
        "computed_at": snapshot.computed_at.isoformat(),
        "components": [
            {"name": c.name, "status": c.status.value} for c in snapshot.system_health.components
        ],
    }
