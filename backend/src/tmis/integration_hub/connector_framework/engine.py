import time

from tmis.integration_hub.connector_framework.ports import (
    ConnectorMetricsRecorderPort,
    ConnectorPort,
)
from tmis.integration_hub.connector_framework.schemas import (
    ConnectorRecord,
    ConnectorWriteResult,
)


class ConnectorInvoker:
    """Wraps every connector call with uniform error handling,
    journalisation and metrics — "gestion des erreurs ; journalisation
    ; métriques" (sprint's minimal connector functions) — so an
    individual connector implementation never reimplements this."""

    def __init__(self, metrics_recorder: ConnectorMetricsRecorderPort) -> None:
        self._metrics_recorder = metrics_recorder

    async def safe_read(
        self,
        connector: ConnectorPort,
        connector_id: str,
        firm_id: str,
        config: dict[str, str],
        since: str | None = None,
    ) -> list[ConnectorRecord]:
        start = time.monotonic()
        try:
            records = await connector.read(config, since)
        except Exception as exc:
            duration_ms = (time.monotonic() - start) * 1000
            self._metrics_recorder.record(
                connector_id,
                firm_id,
                "read",
                success=False,
                duration_ms=duration_ms,
                error=str(exc),
            )
            raise
        duration_ms = (time.monotonic() - start) * 1000
        self._metrics_recorder.record(
            connector_id,
            firm_id,
            "read",
            success=True,
            duration_ms=duration_ms,
            record_count=len(records),
        )
        return records

    async def safe_write(
        self,
        connector: ConnectorPort,
        connector_id: str,
        firm_id: str,
        config: dict[str, str],
        record: ConnectorRecord,
    ) -> ConnectorWriteResult:
        start = time.monotonic()
        try:
            result = await connector.write(config, record)
        except Exception as exc:
            duration_ms = (time.monotonic() - start) * 1000
            self._metrics_recorder.record(
                connector_id,
                firm_id,
                "write",
                success=False,
                duration_ms=duration_ms,
                error=str(exc),
            )
            return ConnectorWriteResult(
                success=False, external_id=record.external_id, detail=str(exc)
            )
        duration_ms = (time.monotonic() - start) * 1000
        self._metrics_recorder.record(
            connector_id,
            firm_id,
            "write",
            success=result.success,
            duration_ms=duration_ms,
            record_count=1,
        )
        return result
