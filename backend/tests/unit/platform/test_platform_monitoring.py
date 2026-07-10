from tmis.platform.health.checks import CallableHealthCheck
from tmis.platform.health.engine import HealthCheckEngine
from tmis.platform.health.schemas import HealthStatus
from tmis.platform.metrics.registry import MetricsRegistry
from tmis.platform.monitoring.engine import MonitoringEngine


class _FakeCostSummary:
    def __init__(self, total: float) -> None:
        self._total = total

    def total_cost_usd(self) -> float:
        return self._total


def test_snapshot_composes_health_metrics_and_cost() -> None:
    health = HealthCheckEngine()
    health.register(CallableHealthCheck("database", lambda: True))
    metrics = MetricsRegistry()
    metrics.counter("http_requests_total", "total").inc(3)

    engine = MonitoringEngine(health, metrics, _FakeCostSummary(12.5))
    snapshot = engine.snapshot()

    assert snapshot.system_health.status is HealthStatus.UP
    assert snapshot.total_requests == 3
    assert snapshot.ai_cost_usd_total == 12.5


def test_snapshot_total_requests_is_zero_when_metric_never_registered() -> None:
    health = HealthCheckEngine()
    metrics = MetricsRegistry()

    engine = MonitoringEngine(health, metrics, _FakeCostSummary(0.0))
    snapshot = engine.snapshot()

    assert snapshot.total_requests == 0.0


def test_snapshot_reflects_a_down_dependency() -> None:
    health = HealthCheckEngine()
    health.register(CallableHealthCheck("queue", lambda: False))
    metrics = MetricsRegistry()

    engine = MonitoringEngine(health, metrics, _FakeCostSummary(0.0))
    snapshot = engine.snapshot()

    assert snapshot.system_health.status is HealthStatus.DOWN
