from datetime import UTC, datetime

from tmis.integration_hub.connector_framework.schemas import (
    ConnectorCapability,
    ConnectorRecord,
    ConnectorType,
    ConnectorWriteResult,
)
from tmis.integration_hub.developer_sdk.base import BaseConnector


class DemoESignatureConnector(BaseConnector):
    """Reference/demo connector for the ESIGNATURE category
    (DocuSign, Yousign, generic e-signature provider...) — no
    vendor-specific business logic, an in-memory dataset only. Meant
    to be replaced by a real vendor adapter implementing the same
    `ConnectorPort` contract."""

    connector_type = ConnectorType.ESIGNATURE
    capabilities = frozenset({ConnectorCapability.READ, ConnectorCapability.WRITE})

    def __init__(self) -> None:
        self._envelopes: list[ConnectorRecord] = [
            ConnectorRecord(
                external_id="env-1",
                data={"document": "Mandat.pdf", "status": "signed"},
                updated_at=datetime.now(UTC),
            )
        ]

    async def read(self, config: dict[str, str], since: str | None = None) -> list[ConnectorRecord]:
        return list(self._envelopes)

    async def write(self, config: dict[str, str], record: ConnectorRecord) -> ConnectorWriteResult:
        self._envelopes.append(record)
        return ConnectorWriteResult(success=True, external_id=record.external_id)
