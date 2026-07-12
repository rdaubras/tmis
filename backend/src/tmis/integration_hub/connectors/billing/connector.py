from datetime import UTC, datetime

from tmis.integration_hub.connector_framework.schemas import (
    ConnectorCapability,
    ConnectorRecord,
    ConnectorType,
    ConnectorWriteResult,
)
from tmis.integration_hub.developer_sdk.base import BaseConnector


class DemoBillingConnector(BaseConnector):
    """Reference/demo connector for the BILLING category (generic
    accounting/invoicing platforms) — no vendor-specific business
    logic, an in-memory dataset only. Meant to be replaced by a real
    vendor adapter implementing the same `ConnectorPort` contract."""

    connector_type = ConnectorType.BILLING
    capabilities = frozenset({ConnectorCapability.READ, ConnectorCapability.WRITE})

    def __init__(self) -> None:
        self._invoices: list[ConnectorRecord] = [
            ConnectorRecord(
                external_id="inv-1",
                data={"client": "Société Dupont SARL", "amount": "4200.00"},
                updated_at=datetime.now(UTC),
            )
        ]

    async def read(self, config: dict[str, str], since: str | None = None) -> list[ConnectorRecord]:
        return list(self._invoices)

    async def write(self, config: dict[str, str], record: ConnectorRecord) -> ConnectorWriteResult:
        self._invoices.append(record)
        return ConnectorWriteResult(success=True, external_id=record.external_id)
