from datetime import UTC, datetime

from tmis.integration_hub.connector_framework.schemas import (
    ConnectorCapability,
    ConnectorRecord,
    ConnectorType,
    ConnectorWriteResult,
)
from tmis.integration_hub.developer_sdk.base import BaseConnector


class DemoDocumentStorageConnector(BaseConnector):
    """Reference/demo connector for the DOCUMENT_STORAGE category
    (SharePoint, Google Drive, generic S3-compatible storage...) — no
    vendor-specific business logic, an in-memory dataset only. Meant
    to be replaced by a real vendor adapter implementing the same
    `ConnectorPort` contract."""

    connector_type = ConnectorType.DOCUMENT_STORAGE
    capabilities = frozenset({ConnectorCapability.READ, ConnectorCapability.WRITE})

    def __init__(self) -> None:
        self._files: list[ConnectorRecord] = [
            ConnectorRecord(
                external_id="doc-1",
                data={"name": "Conclusions.pdf", "folder": "dossier-2026-014"},
                updated_at=datetime.now(UTC),
            )
        ]

    async def read(self, config: dict[str, str], since: str | None = None) -> list[ConnectorRecord]:
        return list(self._files)

    async def write(self, config: dict[str, str], record: ConnectorRecord) -> ConnectorWriteResult:
        self._files.append(record)
        return ConnectorWriteResult(success=True, external_id=record.external_id)
