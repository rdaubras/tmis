from tmis.platform.health.checks import CallableHealthCheck
from tmis.platform.health.engine import HealthCheckEngine
from tmis.platform.health.schemas import HealthStatus


def test_liveness_never_probes_a_registered_check() -> None:
    engine = HealthCheckEngine()
    calls = []
    engine.register(CallableHealthCheck("database", lambda: calls.append(1) or True))

    result = engine.liveness()

    assert result.status is HealthStatus.UP
    assert calls == []


def test_readiness_is_up_when_every_check_passes() -> None:
    engine = HealthCheckEngine()
    engine.register(CallableHealthCheck("database", lambda: True))
    engine.register(CallableHealthCheck("cache", lambda: True))

    result = engine.readiness()

    assert result.status is HealthStatus.UP
    assert len(result.components) == 2


def test_readiness_is_down_if_any_check_reports_down() -> None:
    engine = HealthCheckEngine()
    engine.register(CallableHealthCheck("database", lambda: True))
    engine.register(CallableHealthCheck("queue", lambda: False))

    result = engine.readiness()

    assert result.status is HealthStatus.DOWN


def test_readiness_treats_a_raising_probe_as_down_not_a_crash() -> None:
    def _broken_probe() -> bool:
        raise RuntimeError("connection refused")

    engine = HealthCheckEngine()
    engine.register(CallableHealthCheck("storage", _broken_probe))

    result = engine.readiness()

    assert result.status is HealthStatus.DOWN
    assert result.components[0].detail == "connection refused"


def test_callable_health_check_reports_latency() -> None:
    check = CallableHealthCheck("cache", lambda: True)

    health = check.check()

    assert health.latency_ms >= 0.0
    assert health.status is HealthStatus.UP
