from datetime import UTC, datetime

from tmis.integration_hub.connector_framework.schemas import (
    ConnectorCapability,
    ConnectorRecord,
    ConnectorType,
    ConnectorWriteResult,
)
from tmis.integration_hub.developer_sdk.base import BaseConnector


class DemoCalendarConnector(BaseConnector):
    """Reference/demo connector for the CALENDAR category (Google
    Calendar, Outlook, generic CalDAV...) — no vendor-specific business
    logic, an in-memory dataset only. Meant to be replaced by a real
    vendor adapter implementing the same `ConnectorPort` contract."""

    connector_type = ConnectorType.CALENDAR
    capabilities = frozenset({ConnectorCapability.READ, ConnectorCapability.WRITE})

    def __init__(self) -> None:
        self._events: list[ConnectorRecord] = [
            ConnectorRecord(
                external_id="evt-1",
                data={"title": "Audience TGI Paris", "case_id": "dossier-2026-014"},
                updated_at=datetime.now(UTC),
            )
        ]

    async def read(self, config: dict[str, str], since: str | None = None) -> list[ConnectorRecord]:
        return list(self._events)

    async def write(self, config: dict[str, str], record: ConnectorRecord) -> ConnectorWriteResult:
        self._events.append(record)
        return ConnectorWriteResult(success=True, external_id=record.external_id)
