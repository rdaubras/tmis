from dataclasses import dataclass

from tmis.ai.connectors.codes_connector import CodesConnector
from tmis.ai.connectors.doctrine_connector import DoctrineConnector
from tmis.ai.connectors.exceptions import ConnectorDisabledError, ConnectorError
from tmis.ai.connectors.jurisprudence_connector import JurisprudenceConnector
from tmis.ai.connectors.ports import ConnectorPort
from tmis.ai.schemas.connector import ConnectorDocument


@dataclass
class ConnectorEntry:
    connector: ConnectorPort
    enabled: bool = True


class ConnectorManager:
    """Registers connectors, activates/deactivates them by configuration,
    and isolates failures so one connector going down never fails the
    whole search (see docs/13-guides-extension.md for how to add one).
    """

    def __init__(self) -> None:
        self._entries: dict[str, ConnectorEntry] = {
            "codes": ConnectorEntry(CodesConnector()),
            "jurisprudence": ConnectorEntry(JurisprudenceConnector()),
            "doctrine": ConnectorEntry(DoctrineConnector()),
        }

    def register(self, name: str, connector: ConnectorPort, *, enabled: bool = True) -> None:
        self._entries[name] = ConnectorEntry(connector, enabled=enabled)

    def enable(self, name: str) -> None:
        self._entries[name].enabled = True

    def disable(self, name: str) -> None:
        self._entries[name].enabled = False

    def is_enabled(self, name: str) -> bool:
        return name in self._entries and self._entries[name].enabled

    def list_connectors(self) -> list[str]:
        return list(self._entries)

    async def search(
        self,
        query: str,
        *,
        filters: dict[str, object] | None = None,
        connector_names: list[str] | None = None,
    ) -> list[ConnectorDocument]:
        """Fan out a search to every enabled connector (or the requested
        subset), skipping any connector that errors so a single outage
        degrades gracefully instead of failing the whole request."""
        targets = connector_names or list(self._entries)
        results: list[ConnectorDocument] = []
        for name in targets:
            entry = self._entries.get(name)
            if entry is None or not entry.enabled:
                continue
            try:
                results.extend(await entry.connector.search(query, filters))
            except ConnectorError:
                continue
        return results

    async def fetch(self, connector_name: str, document_id: str) -> ConnectorDocument | None:
        entry = self._entries.get(connector_name)
        if entry is None:
            raise ConnectorError(connector_name, "unknown connector")
        if not entry.enabled:
            raise ConnectorDisabledError(connector_name, "connector is disabled")
        return await entry.connector.fetch(document_id)
