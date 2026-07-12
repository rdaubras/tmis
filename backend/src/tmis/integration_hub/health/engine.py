from tmis.integration_hub.connector_registry.engine import ConnectorRegistryEngine
from tmis.integration_hub.connector_registry.schemas import ConnectorStatus
from tmis.platform.health.checks import CallableHealthCheck
from tmis.platform.health.engine import HealthCheckEngine


class ConnectorHealthProbe:
    """Adapts a registered connector's descriptor status to
    `CallableHealthCheck`'s boolean probe shape — a connector is
    healthy while its descriptor is ACTIVE."""

    def __init__(self, registry: ConnectorRegistryEngine, connector_id: str) -> None:
        self._registry = registry
        self._connector_id = connector_id

    def __call__(self) -> bool:
        descriptor = self._registry.get_descriptor(self._connector_id)
        return descriptor.status is ConnectorStatus.ACTIVE


def register_connector_health_checks(
    engine: HealthCheckEngine, registry: ConnectorRegistryEngine
) -> None:
    """Registers one `CallableHealthCheck` per connector currently in
    the registry — the LIH never reimplements liveness/readiness
    aggregation, it composes `tmis.platform.health` directly (already
    built once at Sprint 10)."""

    for descriptor in registry.list_connectors():
        engine.register(
            CallableHealthCheck(
                f"connector:{descriptor.id}", ConnectorHealthProbe(registry, descriptor.id)
            )
        )
