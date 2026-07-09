class ConnectorError(Exception):
    """Raised when a connector call fails. Carries the connector name so
    the `ConnectorManager` can degrade gracefully (skip the failing
    connector, keep results from the others) instead of failing the whole
    request."""

    def __init__(self, connector_name: str, message: str) -> None:
        super().__init__(f"[{connector_name}] {message}")
        self.connector_name = connector_name


class ConnectorAuthenticationError(ConnectorError):
    """Raised when a connector's configured credentials are invalid or missing."""


class ConnectorDisabledError(ConnectorError):
    """Raised when a caller targets a connector that is disabled in configuration."""
