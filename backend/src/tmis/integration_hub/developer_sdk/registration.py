from tmis.integration_hub.connector_framework.ports import ConnectorPort
from tmis.integration_hub.connector_registry.engine import ConnectorRegistryEngine
from tmis.integration_hub.connector_registry.schemas import ConnectorDescriptor


def register_connector(
    registry: ConnectorRegistryEngine,
    implementation: ConnectorPort,
    *,
    connector_id: str,
    name: str,
    version: str,
    publisher: str,
    permissions: tuple[str, ...] = (),
    config_schema: dict[str, str] | None = None,
) -> ConnectorDescriptor:
    """One-call connector installation for the SDK's quick-start path
    — wraps `ConnectorDescriptor` construction plus
    `ConnectorRegistryEngine.register()`."""
    descriptor = ConnectorDescriptor(
        id=connector_id,
        name=name,
        version=version,
        publisher=publisher,
        connector_type=implementation.connector_type,
        capabilities=frozenset(implementation.capabilities),
        permissions=permissions,
        config_schema=config_schema or {},
    )
    registry.register(descriptor, implementation)
    return descriptor
