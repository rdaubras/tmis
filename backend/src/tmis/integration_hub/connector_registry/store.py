from tmis.integration_hub.connector_registry.schemas import ConnectorDescriptor


class InMemoryConnectorRegistryStore:
    def __init__(self) -> None:
        self._descriptors: dict[str, ConnectorDescriptor] = {}

    def add(self, descriptor: ConnectorDescriptor) -> None:
        self._descriptors[descriptor.id] = descriptor

    def get(self, connector_id: str) -> ConnectorDescriptor | None:
        return self._descriptors.get(connector_id)

    def list_all(self) -> list[ConnectorDescriptor]:
        return list(self._descriptors.values())
