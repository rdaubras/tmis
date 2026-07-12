from typing import Protocol

from tmis.integration_hub.connector_registry.schemas import ConnectorDescriptor


class ConnectorRegistryStorePort(Protocol):
    def add(self, descriptor: ConnectorDescriptor) -> None: ...

    def get(self, connector_id: str) -> ConnectorDescriptor | None: ...

    def list_all(self) -> list[ConnectorDescriptor]: ...
