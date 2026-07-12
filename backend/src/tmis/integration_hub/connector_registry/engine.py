from tmis.integration_hub.connector_framework.ports import ConnectorPort
from tmis.integration_hub.connector_registry.ports import ConnectorRegistryStorePort
from tmis.integration_hub.connector_registry.schemas import ConnectorDescriptor, ConnectorStatus


class ConnectorRegistryEngine:
    """Registers connector implementations alongside their
    descriptor — "prévoir l'installation dynamique" (sprint
    requirement): `register()` can be called at any time, including
    after startup, without a redeploy."""

    def __init__(self, store: ConnectorRegistryStorePort) -> None:
        self._store = store
        self._implementations: dict[str, ConnectorPort] = {}

    def register(self, descriptor: ConnectorDescriptor, implementation: ConnectorPort) -> None:
        self._store.add(descriptor)
        self._implementations[descriptor.id] = implementation

    def get_descriptor(self, connector_id: str) -> ConnectorDescriptor:
        descriptor = self._store.get(connector_id)
        if descriptor is None:
            raise KeyError(connector_id)
        return descriptor

    def get_implementation(self, connector_id: str) -> ConnectorPort:
        implementation = self._implementations.get(connector_id)
        if implementation is None:
            raise KeyError(connector_id)
        return implementation

    def list_connectors(
        self, connector_type: str | None = None, status: ConnectorStatus | None = None
    ) -> list[ConnectorDescriptor]:
        descriptors = self._store.list_all()
        if connector_type is not None:
            descriptors = [d for d in descriptors if d.connector_type == connector_type]
        if status is not None:
            descriptors = [d for d in descriptors if d.status == status]
        return descriptors

    def disable(self, connector_id: str) -> ConnectorDescriptor:
        descriptor = self.get_descriptor(connector_id)
        descriptor.status = ConnectorStatus.DISABLED
        return descriptor

    def enable(self, connector_id: str) -> ConnectorDescriptor:
        descriptor = self.get_descriptor(connector_id)
        descriptor.status = ConnectorStatus.ACTIVE
        return descriptor
