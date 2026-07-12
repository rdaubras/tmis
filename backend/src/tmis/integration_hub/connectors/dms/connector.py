from datetime import UTC, datetime

from tmis.integration_hub.connector_framework.schemas import (
    ConnectorCapability,
    ConnectorRecord,
    ConnectorType,
    ConnectorWriteResult,
)
from tmis.integration_hub.developer_sdk.base import BaseConnector


class DemoDmsConnector(BaseConnector):
    """Reference/demo connector for the DMS category (legacy
    document-management systems, generic case-file repositories...) —
    no vendor-specific business logic, an in-memory dataset only.
    Meant to be replaced by a real vendor adapter implementing the
    same `ConnectorPort` contract."""

    connector_type = ConnectorType.DMS
    capabilities = frozenset({ConnectorCapability.READ, ConnectorCapability.WRITE})

    def __init__(self) -> None:
        self._records: list[ConnectorRecord] = [
            ConnectorRecord(
                external_id="dms-1",
                data={"reference": "DOS-2026-014", "matter": "Litige commercial"},
                updated_at=datetime.now(UTC),
            )
        ]

    async def read(self, config: dict[str, str], since: str | None = None) -> list[ConnectorRecord]:
        return list(self._records)

    async def write(self, config: dict[str, str], record: ConnectorRecord) -> ConnectorWriteResult:
        self._records.append(record)
        return ConnectorWriteResult(success=True, external_id=record.external_id)
