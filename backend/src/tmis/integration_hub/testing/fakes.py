from tmis.integration_hub.connector_framework.schemas import (
    ConnectorCapability,
    ConnectorRecord,
    ConnectorType,
    ConnectorWriteResult,
)


class InMemoryFakeConnector:
    """A minimal in-memory `ConnectorPort` implementation for tests —
    "fournir un harnais de test pour valider un connecteur sans
    dépendre d'un système externe réel" (sprint requirement). Seed it
    with `records` and inspect `written` to assert what a sync job
    pushed."""

    connector_type = ConnectorType.OTHER
    capabilities = frozenset({ConnectorCapability.READ, ConnectorCapability.WRITE})

    def __init__(
        self, records: list[ConnectorRecord] | None = None, *, fail_auth: bool = False
    ) -> None:
        self.records = list(records) if records is not None else []
        self.written: list[ConnectorRecord] = []
        self.fail_auth = fail_auth

    async def authenticate(self, config: dict[str, str]) -> bool:
        return not self.fail_auth

    async def read(self, config: dict[str, str], since: str | None = None) -> list[ConnectorRecord]:
        return list(self.records)

    async def write(self, config: dict[str, str], record: ConnectorRecord) -> ConnectorWriteResult:
        self.written.append(record)
        return ConnectorWriteResult(success=True, external_id=record.external_id)


class NoOpMetricsRecorder:
    """A `ConnectorMetricsRecorderPort` that discards every reading —
    handy for tests that don't care about monitoring output."""

    def record(
        self,
        connector_id: str,
        firm_id: str,
        operation: str,
        *,
        success: bool,
        duration_ms: float,
        record_count: int = 0,
        error: str | None = None,
    ) -> None:
        return None
