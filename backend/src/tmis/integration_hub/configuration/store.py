from tmis.integration_hub.configuration.schemas import ConnectorConfiguration


class InMemoryConnectorConfigurationStore:
    def __init__(self) -> None:
        self._configurations: dict[tuple[str, str], ConnectorConfiguration] = {}

    def save(self, configuration: ConnectorConfiguration) -> None:
        self._configurations[(configuration.firm_id, configuration.connector_id)] = configuration

    def get(self, firm_id: str, connector_id: str) -> ConnectorConfiguration | None:
        return self._configurations.get((firm_id, connector_id))
