from datetime import UTC, datetime

from tmis.integration_hub.connector_framework.schemas import (
    ConnectorCapability,
    ConnectorRecord,
    ConnectorType,
    ConnectorWriteResult,
)
from tmis.integration_hub.developer_sdk.base import BaseConnector


class DemoCrmConnector(BaseConnector):
    """Reference/demo connector for the CRM category (generic client
    relationship management systems) — no vendor-specific business
    logic, an in-memory dataset only. Meant to be replaced by a real
    vendor adapter implementing the same `ConnectorPort` contract."""

    connector_type = ConnectorType.CRM
    capabilities = frozenset({ConnectorCapability.READ, ConnectorCapability.WRITE})

    def __init__(self) -> None:
        self._clients: list[ConnectorRecord] = [
            ConnectorRecord(
                external_id="cli-1",
                data={"name": "Société Dupont SARL", "segment": "Corporate"},
                updated_at=datetime.now(UTC),
            )
        ]

    async def read(self, config: dict[str, str], since: str | None = None) -> list[ConnectorRecord]:
        return list(self._clients)

    async def write(self, config: dict[str, str], record: ConnectorRecord) -> ConnectorWriteResult:
        self._clients.append(record)
        return ConnectorWriteResult(success=True, external_id=record.external_id)
