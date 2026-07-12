from abc import ABC

from tmis.integration_hub.connector_framework.schemas import (
    ConnectorCapability,
    ConnectorRecord,
    ConnectorType,
    ConnectorWriteResult,
)


class BaseConnector(ABC):
    """The sprint's "SDK développeur" base class: implements
    `connector_framework.ports.ConnectorPort` with sensible defaults
    so a new connector only declares `connector_type`/`capabilities`
    and overrides the operations it actually supports — "créer un
    nouveau connecteur doit être simple et rapide, sans dépendance
    forte à un fournisseur" (sprint requirement). Distinct from
    `platform_sdk.connector_sdk.BaseConnectorPlugin` — see
    `connector_framework.ports.ConnectorPort` for the naming-collision
    rationale."""

    connector_type: ConnectorType
    capabilities: frozenset[ConnectorCapability] = frozenset()

    async def authenticate(self, config: dict[str, str]) -> bool:
        return True

    async def read(
        self, config: dict[str, str], since: str | None = None
    ) -> list[ConnectorRecord]:
        raise NotImplementedError(f"{type(self).__name__} does not support read")

    async def write(
        self, config: dict[str, str], record: ConnectorRecord
    ) -> ConnectorWriteResult:
        raise NotImplementedError(f"{type(self).__name__} does not support write")
