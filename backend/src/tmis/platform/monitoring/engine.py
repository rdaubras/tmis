from datetime import UTC, datetime

from tmis.platform.health.ports import HealthCheckEnginePort
from tmis.platform.metrics.registry import Counter, MetricsRegistry
from tmis.platform.monitoring.ports import CostSummaryPort
from tmis.platform.monitoring.schemas import SupervisionDashboard


class MonitoringEngine:
    """Implements `MonitoringEnginePort` (see
    docs/49-guide-supervision.md — Tableaux de bord de supervision):
    composes `HealthCheckEnginePort`, `MetricsRegistry`, and a narrow
    `CostSummaryPort` into one snapshot, without owning any of that
    data itself."""

    def __init__(
        self,
        health_engine: HealthCheckEnginePort,
        metrics_registry: MetricsRegistry,
        cost_summary: CostSummaryPort,
    ) -> None:
        self._health = health_engine
        self._metrics = metrics_registry
        self._cost_summary = cost_summary

    def snapshot(self) -> SupervisionDashboard:
        system_health = self._health.readiness()
        requests_metric = self._metrics.try_get("http_requests_total")
        total_requests = (
            requests_metric.total() if isinstance(requests_metric, Counter) else 0.0
        )
        return SupervisionDashboard(
            system_health=system_health,
            total_requests=total_requests,
            ai_cost_usd_total=self._cost_summary.total_cost_usd(),
            computed_at=datetime.now(UTC),
        )
