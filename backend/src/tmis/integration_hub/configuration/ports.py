from typing import Protocol

from tmis.integration_hub.configuration.schemas import ConnectorConfiguration


class ConnectorConfigurationStorePort(Protocol):
    def save(self, configuration: ConnectorConfiguration) -> None: ...

    def get(self, firm_id: str, connector_id: str) -> ConnectorConfiguration | None: ...
