import time
from datetime import UTC, datetime

from tmis.integration_hub.conflict_resolution.engine import ConflictResolutionEngine
from tmis.integration_hub.conflict_resolution.schemas import ConflictContext
from tmis.integration_hub.connector_framework.engine import ConnectorInvoker
from tmis.integration_hub.connector_framework.ports import ConnectorPort
from tmis.integration_hub.connector_framework.schemas import ConnectorSyncResult
from tmis.integration_hub.monitoring.engine import ConnectorMonitoringEngine
from tmis.integration_hub.synchronization.ports import LocalRecordLookupPort, MapperPort
from tmis.integration_hub.synchronization.schemas import SyncJobConfig, SyncMode, SyncRunReport


class SynchronizationEngine:
    """Runs one configurable sync job — "toutes les synchronisations
    sont configurables" (sprint requirement). Depends only on narrow
    ports for field mapping (`MapperPort`) and local-record lookup
    (`LocalRecordLookupPort`) so it can be built and tested before
    `integration_hub.mapping` and any domain bounded context exist —
    same decoupled-input pattern as
    `workflow_automation.trigger_engine`."""

    def __init__(
        self,
        invoker: ConnectorInvoker,
        conflict_engine: ConflictResolutionEngine,
        monitoring: ConnectorMonitoringEngine | None = None,
    ) -> None:
        self._invoker = invoker
        self._conflict_engine = conflict_engine
        self._monitoring = monitoring

    async def run_pull(
        self,
        job: SyncJobConfig,
        connector: ConnectorPort,
        config: dict[str, str],
        mapper: MapperPort | None = None,
        local_lookup: LocalRecordLookupPort | None = None,
    ) -> SyncRunReport:
        started = time.perf_counter()
        try:
            report = await self._run_pull(job, connector, config, mapper, local_lookup)
        except Exception as exc:
            self._record_operation(job, 0, success=False, started=started, error=str(exc))
            raise
        self._record_operation(job, report.result.records_written, success=True, started=started)
        return report

    async def _run_pull(
        self,
        job: SyncJobConfig,
        connector: ConnectorPort,
        config: dict[str, str],
        mapper: MapperPort | None,
        local_lookup: LocalRecordLookupPort | None,
    ) -> SyncRunReport:
        since = (
            job.last_synced_at.isoformat()
            if job.mode is SyncMode.INCREMENTAL and job.last_synced_at is not None
            else None
        )
        records = await self._invoker.safe_read(
            connector, job.connector_id, job.firm_id, config, since=since
        )

        written = 0
        conflicts = 0
        pending = 0
        for record in records:
            mapped = mapper.map(record, job.entity_type) if mapper is not None else record
            local = (
                local_lookup.find(job.firm_id, job.entity_type, mapped.external_id)
                if local_lookup is not None
                else None
            )
            if local is not None and local.data != mapped.data:
                resolution = self._conflict_engine.resolve(
                    ConflictContext(
                        connector_id=job.connector_id,
                        firm_id=job.firm_id,
                        entity_type=job.entity_type,
                        external_id=mapped.external_id,
                        local_record=local,
                        remote_record=mapped,
                    ),
                    job.conflict_strategy,
                )
                conflicts += 1
                if resolution.pending_human_validation:
                    pending += 1
                    continue
            written += 1

        job.last_synced_at = datetime.now(UTC)
        result = ConnectorSyncResult(
            records_read=len(records), records_written=written, conflicts=conflicts
        )
        return SyncRunReport(job_id=job.id, result=result, conflicts_pending_validation=pending)

    def _record_operation(
        self,
        job: SyncJobConfig,
        record_count: int,
        *,
        success: bool,
        started: float,
        error: str | None = None,
    ) -> None:
        if self._monitoring is None:
            return
        self._monitoring.record(
            job.connector_id,
            job.firm_id,
            "pull",
            success=success,
            duration_ms=(time.perf_counter() - started) * 1000,
            record_count=record_count,
            error=error,
        )
