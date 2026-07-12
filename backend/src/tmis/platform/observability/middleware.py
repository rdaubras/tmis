import time
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response

from tmis.platform.metrics.bootstrap import get_metrics_registry

_TRACE_ID_STATE_ATTR = "trace_id"


async def correlation_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Binds the trace id (already set on `request.state` by
    `tmis.core.observability.trace_id_middleware`, which must run
    first) into structlog's contextvars, so every log line emitted
    while handling this request — at any call depth — carries the same
    `trace_id` without threading it through every function signature
    (see docs/49-guide-supervision.md — Corrélation des requêtes)."""
    trace_id = getattr(request.state, _TRACE_ID_STATE_ATTR, None)
    structlog.contextvars.clear_contextvars()
    if trace_id is not None:
        structlog.contextvars.bind_contextvars(trace_id=trace_id)
    try:
        return await call_next(request)
    finally:
        structlog.contextvars.clear_contextvars()


async def metrics_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Records one HTTP request: a `Counter` by method/path/status and
    a `Histogram` of duration by path — the metrics behind
    `GET /platform/metrics` (see docs/49-guide-supervision.md —
    Métriques)."""
    registry = get_metrics_registry()
    route_path = request.url.path
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    registry.counter("http_requests_total", "Total HTTP requests").inc(
        method=request.method, path=route_path, status=str(response.status_code)
    )
    registry.histogram("http_request_duration_seconds", "HTTP request duration in seconds").observe(
        duration, path=route_path
    )
    _record_cloud_operations_telemetry(request, response, duration * 1000)
    return response


def _record_cloud_operations_telemetry(
    request: Request, response: Response, duration_ms: float
) -> None:
    """Publishes the "API" hop of the sprint's end-to-end request
    trace (Utilisateur → API → Workflow → AI Fabric → ...) for every
    request TMIS serves: a `RESPONSE_TIME` sample plus an `API` span
    under the same `trace_id` `core.observability.trace_id_middleware`
    already attached to `request.state` — every downstream hop that
    also reports under that `trace_id` (see `workflow_automation.
    execution_engine.ExecutionEngine._record_started`) shows up as one
    connected trace. A local import avoids a hard dependency from
    `platform` on `cloud_operations` at module-import time."""
    from tmis.cloud_operations.bootstrap import get_metrics_engine, get_tracing_engine
    from tmis.cloud_operations.metrics.schemas import MetricCategory
    from tmis.cloud_operations.tracing.schemas import SpanKind, SpanStatus

    route_path = request.url.path
    if route_path.startswith("/cloud-operations"):
        return  # avoid instrumenting the observability API's own traffic

    get_metrics_engine().record(MetricCategory.RESPONSE_TIME, route_path, duration_ms)

    trace_id = getattr(request.state, _TRACE_ID_STATE_ATTR, None)
    if trace_id is None:
        return
    tracing = get_tracing_engine()
    span = tracing.start_span(
        trace_id,
        SpanKind.API,
        f"{request.method} {route_path}",
        attributes={"status_code": str(response.status_code)},
    )
    status = SpanStatus.ERROR if response.status_code >= 500 else SpanStatus.OK
    tracing.end_span(span.id, status=status)
