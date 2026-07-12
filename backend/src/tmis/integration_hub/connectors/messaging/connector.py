from datetime import UTC, datetime

from tmis.integration_hub.connector_framework.schemas import (
    ConnectorCapability,
    ConnectorRecord,
    ConnectorType,
    ConnectorWriteResult,
)
from tmis.integration_hub.developer_sdk.base import BaseConnector


class DemoMessagingConnector(BaseConnector):
    """Reference/demo connector for the MESSAGING category (Slack,
    Teams, generic webhook-based chat...) — no vendor-specific
    business logic, an in-memory dataset only. Meant to be replaced by
    a real vendor adapter that implements the same `ConnectorPort`
    contract; nothing outside this file needs to change to swap it
    in."""

    connector_type = ConnectorType.MESSAGING
    capabilities = frozenset({ConnectorCapability.READ, ConnectorCapability.WRITE})

    def __init__(self) -> None:
        self._messages: list[ConnectorRecord] = [
            ConnectorRecord(
                external_id="msg-1",
                data={
                    "channel": "dossier-2026-014",
                    "author": "avocat.dupont",
                    "text": "Audience confirmée pour le 20/07.",
                },
                updated_at=datetime.now(UTC),
            )
        ]

    async def read(self, config: dict[str, str], since: str | None = None) -> list[ConnectorRecord]:
        return list(self._messages)

    async def write(self, config: dict[str, str], record: ConnectorRecord) -> ConnectorWriteResult:
        self._messages.append(record)
        return ConnectorWriteResult(success=True, external_id=record.external_id)
