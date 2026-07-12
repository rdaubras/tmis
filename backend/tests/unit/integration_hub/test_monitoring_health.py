from tmis.integration_hub.connector_framework import (
    ConnectorCapability,
    ConnectorRecord,
    ConnectorType,
    ConnectorWriteResult,
)
from tmis.integration_hub.connector_registry import (
    ConnectorDescriptor,
    ConnectorRegistryEngine,
    InMemoryConnectorRegistryStore,
)
from tmis.integration_hub.health import register_connector_health_checks
from tmis.integration_hub.monitoring import ConnectorMonitoringEngine, InMemoryConnectorMetricsSink
from tmis.platform.health.engine import HealthCheckEngine
from tmis.platform.health.schemas import HealthStatus


def test_connector_monitoring_engine_fans_out_to_sinks() -> None:
    sink1 = InMemoryConnectorMetricsSink()
    sink2 = InMemoryConnectorMetricsSink()
    engine = ConnectorMonitoringEngine([sink1, sink2])

    engine.record("c1", "f1", "read", success=True, duration_ms=12.5, record_count=3)

    for sink in (sink1, sink2):
        metrics = sink.for_connector("c1")
        assert len(metrics) == 1
        assert metrics[0].success is True
        assert metrics[0].record_count == 3


def test_metrics_sink_success_rate() -> None:
    sink = InMemoryConnectorMetricsSink()
    engine = ConnectorMonitoringEngine([sink])
    engine.record("c1", "f1", "read", success=True, duration_ms=1.0)
    engine.record("c1", "f1", "read", success=False, duration_ms=1.0, error="boom")

    assert sink.success_rate("c1") == 0.5


def test_metrics_sink_success_rate_no_metrics_defaults_to_one() -> None:
    sink = InMemoryConnectorMetricsSink()
    assert sink.success_rate("unknown") == 1.0


def _make_registry() -> ConnectorRegistryEngine:
    class _FakeConnector:
        connector_type = ConnectorType.CRM
        capabilities = frozenset({ConnectorCapability.READ})

        async def authenticate(self, config: dict[str, str]) -> bool:
            return True

        async def read(
            self, config: dict[str, str], since: str | None = None
        ) -> list[ConnectorRecord]:
            return []

        async def write(
            self, config: dict[str, str], record: ConnectorRecord
        ) -> ConnectorWriteResult:
            raise NotImplementedError

    registry = ConnectorRegistryEngine(InMemoryConnectorRegistryStore())
    descriptor = ConnectorDescriptor(
        id="c1", name="Fake", version="1.0", publisher="TMIS",
        connector_type=ConnectorType.CRM, capabilities=frozenset({ConnectorCapability.READ}),
    )
    registry.register(descriptor, _FakeConnector())
    return registry


def test_register_connector_health_checks_reports_up_for_active_connectors() -> None:
    registry = _make_registry()
    engine = HealthCheckEngine()
    register_connector_health_checks(engine, registry)

    result = engine.readiness()
    assert result.status is HealthStatus.UP
    assert len(result.components) == 1
    assert result.components[0].name == "connector:c1"


def test_register_connector_health_checks_reports_down_when_disabled() -> None:
    registry = _make_registry()
    engine = HealthCheckEngine()
    register_connector_health_checks(engine, registry)

    registry.disable("c1")
    result = engine.readiness()
    assert result.status is HealthStatus.DOWN
