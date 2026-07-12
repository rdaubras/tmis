from tmis.integration_hub.configuration.ports import ConnectorConfigurationStorePort
from tmis.integration_hub.configuration.schemas import ConnectorConfiguration
from tmis.integration_hub.connector_registry.schemas import ConnectorDescriptor


class ConfigurationValidationError(ValueError):
    pass


class ConfigurationEngine:
    """Validates and stores per-firm connector configuration against
    the connector's declared `config_schema` — "chaque intégration est
    configurable indépendamment par le cabinet, sans dépendance forte
    à un fournisseur" (sprint requirement)."""

    def __init__(self, store: ConnectorConfigurationStorePort) -> None:
        self._store = store

    def set_configuration(
        self,
        connector_id: str,
        firm_id: str,
        values: dict[str, str],
        descriptor: ConnectorDescriptor | None = None,
    ) -> ConnectorConfiguration:
        if descriptor is not None:
            missing = [key for key in descriptor.config_schema if key not in values]
            if missing:
                raise ConfigurationValidationError(
                    f"Champs de configuration manquants : {', '.join(missing)}"
                )
        configuration = ConnectorConfiguration(
            connector_id=connector_id, firm_id=firm_id, values=values
        )
        self._store.save(configuration)
        return configuration

    def get_configuration(self, firm_id: str, connector_id: str) -> ConnectorConfiguration | None:
        return self._store.get(firm_id, connector_id)
