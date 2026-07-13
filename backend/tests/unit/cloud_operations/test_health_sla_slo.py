from tmis.cloud_operations.sla.engine import SLAEngine
from tmis.cloud_operations.sla.schemas import SLAMetricType
from tmis.cloud_operations.sla.store import InMemorySLASampleStore, InMemorySLATargetStore
from tmis.cloud_operations.slo.engine import SLOEngine
from tmis.cloud_operations.slo.store import InMemorySLOTargetStore
from tmis.platform.health.checks import CallableHealthCheck
from tmis.platform.health.engine import HealthCheckEngine
from tmis.platform.health.schemas import HealthStatus


def test_health_check_engine_aggregates_registered_checks() -> None:
    engine = HealthCheckEngine()
    engine.register(CallableHealthCheck("ai_fabric", lambda: True))
    engine.register(CallableHealthCheck("marketplace", lambda: False))

    health = engine.readiness()
    assert health.status is HealthStatus.DOWN
    assert {c.name for c in health.components} == {"ai_fabric", "marketplace"}


def _sla_engine() -> SLAEngine:
    return SLAEngine(InMemorySLATargetStore(), InMemorySLASampleStore())


def test_sla_engine_computes_indicator_for_latency_lower_is_better() -> None:
    engine = _sla_engine()
    engine.set_target("api", SLAMetricType.LATENCY, 200.0)
    engine.record_sample("api", SLAMetricType.LATENCY, 150.0)
    engine.record_sample("api", SLAMetricType.LATENCY, 250.0)

    indicator = engine.compute_indicator("api", SLAMetricType.LATENCY)
    assert indicator is not None
    assert indicator.actual_value == 200.0
    assert indicator.met is True


def test_sla_engine_computes_indicator_for_availability_higher_is_better() -> None:
    engine = _sla_engine()
    engine.set_target("api", SLAMetricType.AVAILABILITY, 99.9)
    engine.record_sample("api", SLAMetricType.AVAILABILITY, 99.5)

    indicator = engine.compute_indicator("api", SLAMetricType.AVAILABILITY)
    assert indicator is not None
    assert indicator.met is False


def test_slo_engine_reuses_sla_average_and_computes_error_budget() -> None:
    sla = _sla_engine()
    slo = SLOEngine(InMemorySLOTargetStore(), sla)
    slo.set_objective("api", SLAMetricType.SUCCESS_RATE, 99.0)
    sla.record_sample("api", SLAMetricType.SUCCESS_RATE, 99.5)

    status = slo.status("api", SLAMetricType.SUCCESS_RATE)
    assert status is not None
    assert status.at_risk is False
    assert status.error_budget_remaining_percent == 100.0


def test_slo_engine_returns_none_without_samples() -> None:
    sla = _sla_engine()
    slo = SLOEngine(InMemorySLOTargetStore(), sla)
    slo.set_objective("api", SLAMetricType.LATENCY, 200.0)
    assert slo.status("api", SLAMetricType.LATENCY) is None
