from datetime import UTC, datetime

import pytest

from tmis.ai_governance.human_validation.engine import HumanValidationEngine
from tmis.ai_governance.human_validation.schemas import ValidationDecisionType
from tmis.ai_governance.human_validation.store import InMemoryValidationStore
from tmis.integration_hub.conflict_resolution import (
    ConflictContext,
    ConflictResolutionEngine,
    ConflictStrategy,
    HumanValidationStrategy,
)
from tmis.integration_hub.connector_framework import (
    ConnectorCapability,
    ConnectorInvoker,
    ConnectorRecord,
    ConnectorType,
    ConnectorWriteResult,
)
from tmis.integration_hub.synchronization import (
    InMemorySyncJobStore,
    SyncDirection,
    SynchronizationEngine,
    SyncJobConfig,
    SyncMode,
)


def _record(external_id: str, data: dict[str, str]) -> ConnectorRecord:
    return ConnectorRecord(external_id=external_id, data=data, updated_at=datetime.now(UTC))


def test_local_wins_strategy() -> None:
    engine = ConflictResolutionEngine()
    context = ConflictContext(
        connector_id="c1",
        firm_id="f1",
        entity_type="client",
        external_id="e1",
        local_record=_record("e1", {"name": "local"}),
        remote_record=_record("e1", {"name": "remote"}),
    )
    resolution = engine.resolve(context, ConflictStrategy.LOCAL_WINS)
    assert resolution.resolved_record is not None
    assert resolution.resolved_record.data["name"] == "local"


def test_remote_wins_strategy() -> None:
    engine = ConflictResolutionEngine()
    context = ConflictContext(
        connector_id="c1",
        firm_id="f1",
        entity_type="client",
        external_id="e1",
        local_record=_record("e1", {"name": "local"}),
        remote_record=_record("e1", {"name": "remote"}),
    )
    resolution = engine.resolve(context, ConflictStrategy.REMOTE_WINS)
    assert resolution.resolved_record is not None
    assert resolution.resolved_record.data["name"] == "remote"


def test_last_write_wins_strategy_picks_most_recent() -> None:
    engine = ConflictResolutionEngine()
    older = ConnectorRecord(
        external_id="e1", data={"name": "older"}, updated_at=datetime(2020, 1, 1, tzinfo=UTC)
    )
    newer = ConnectorRecord(
        external_id="e1", data={"name": "newer"}, updated_at=datetime(2025, 1, 1, tzinfo=UTC)
    )
    context = ConflictContext(
        connector_id="c1", firm_id="f1", entity_type="client", external_id="e1",
        local_record=older, remote_record=newer,
    )
    resolution = engine.resolve(context, ConflictStrategy.LAST_WRITE_WINS)
    assert resolution.resolved_record is not None
    assert resolution.resolved_record.data["name"] == "newer"


def test_human_validation_strategy_pending_then_approved() -> None:
    validation_engine = HumanValidationEngine(InMemoryValidationStore())
    strategy = HumanValidationStrategy(validation_engine, ("partner-1",))
    engine = ConflictResolutionEngine({ConflictStrategy.HUMAN_VALIDATION: strategy})
    context = ConflictContext(
        connector_id="c1",
        firm_id="f1",
        entity_type="client",
        external_id="e1",
        local_record=_record("e1", {"name": "local"}),
        remote_record=_record("e1", {"name": "remote"}),
    )

    first = engine.resolve(context, ConflictStrategy.HUMAN_VALIDATION)
    assert first.pending_human_validation is True
    assert first.resolved_record is None

    requests = validation_engine.history("f1", "c1:e1")
    assert len(requests) == 1
    validation_engine.decide("f1", requests[0].id, "partner-1", ValidationDecisionType.APPROVE)

    second = engine.resolve(context, ConflictStrategy.HUMAN_VALIDATION)
    assert second.pending_human_validation is False
    assert second.resolved_record is not None
    assert second.resolved_record.data["name"] == "remote"


def test_unknown_conflict_strategy_raises() -> None:
    engine = ConflictResolutionEngine()
    context = ConflictContext(
        connector_id="c1", firm_id="f1", entity_type="client", external_id="e1",
        local_record=_record("e1", {}), remote_record=_record("e1", {}),
    )
    with pytest.raises(KeyError):
        engine.resolve(context, ConflictStrategy.HUMAN_VALIDATION)


class _FakeConnector:
    connector_type = ConnectorType.CRM
    capabilities = frozenset({ConnectorCapability.READ})

    def __init__(self, records: list[ConnectorRecord]) -> None:
        self.records = records

    async def authenticate(self, config: dict[str, str]) -> bool:
        return True

    async def read(self, config: dict[str, str], since: str | None = None) -> list[ConnectorRecord]:
        return list(self.records)

    async def write(self, config: dict[str, str], record: ConnectorRecord) -> ConnectorWriteResult:
        raise NotImplementedError


class _Metrics:
    def record(self, connector_id: str, firm_id: str, operation: str, *, success: bool,
               duration_ms: float, record_count: int = 0, error: str | None = None) -> None:
        return None


@pytest.mark.asyncio
async def test_synchronization_engine_pull_full_no_conflicts() -> None:
    invoker = ConnectorInvoker(_Metrics())
    sync_engine = SynchronizationEngine(invoker, ConflictResolutionEngine())
    store = InMemorySyncJobStore()
    job = SyncJobConfig(
        id="job-1", connector_id="c1", firm_id="f1", entity_type="client",
        direction=SyncDirection.PULL, mode=SyncMode.FULL,
    )
    store.save(job)

    connector = _FakeConnector([_record("e1", {"name": "a"}), _record("e2", {"name": "b"})])
    report = await sync_engine.run_pull(job, connector, {})

    assert report.result.records_read == 2
    assert report.result.records_written == 2
    assert report.result.conflicts == 0
    assert job.last_synced_at is not None


@pytest.mark.asyncio
async def test_synchronization_engine_pull_detects_and_resolves_conflict() -> None:
    invoker = ConnectorInvoker(_Metrics())
    sync_engine = SynchronizationEngine(invoker, ConflictResolutionEngine())
    store = InMemorySyncJobStore()
    job = SyncJobConfig(
        id="job-1", connector_id="c1", firm_id="f1", entity_type="client",
        direction=SyncDirection.PULL, mode=SyncMode.FULL,
        conflict_strategy=ConflictStrategy.REMOTE_WINS,
    )
    store.save(job)

    connector = _FakeConnector([_record("e1", {"name": "remote"})])

    class _LocalLookup:
        def find(self, firm_id: str, entity_type: str, external_id: str) -> ConnectorRecord | None:
            return _record("e1", {"name": "local"})

    report = await sync_engine.run_pull(job, connector, {}, local_lookup=_LocalLookup())
    assert report.result.conflicts == 1
    assert report.result.records_written == 1
