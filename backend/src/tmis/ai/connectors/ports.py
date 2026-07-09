from typing import Protocol

from tmis.ai.schemas.connector import ConnectorDocument


class ConnectorPort(Protocol):
    """Port implemented by every interchangeable document/data source
    connector (legal codes, jurisprudence, doctrine, and — in the future —
    other internal or external document sources)."""

    connector_name: str

    async def search(
        self, query: str, filters: dict[str, object] | None = None
    ) -> list[ConnectorDocument]: ...

    async def fetch(self, document_id: str) -> ConnectorDocument | None: ...
