from tmis.integration_hub.connector_framework.ports import ConnectorPort
from tmis.integration_hub.connector_framework.schemas import ConnectorCapability


class ConnectorConformanceError(AssertionError):
    pass


async def assert_connector_conforms(connector: ConnectorPort, config: dict[str, str]) -> None:
    """Exercises the `ConnectorPort` operations a connector declares
    support for, raising `ConnectorConformanceError` with a clear
    message on the first violation — "valider qu'un connecteur
    respecte le contrat avant sa mise en production" (sprint
    requirement)."""
    authenticated = await connector.authenticate(config)
    if not isinstance(authenticated, bool):
        raise ConnectorConformanceError("authenticate() must return a bool")

    if ConnectorCapability.READ in connector.capabilities:
        records = await connector.read(config)
        if not isinstance(records, list):
            raise ConnectorConformanceError("read() must return a list[ConnectorRecord]")
