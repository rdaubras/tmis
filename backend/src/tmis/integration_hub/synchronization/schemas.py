from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from tmis.integration_hub.conflict_resolution.schemas import ConflictStrategy
from tmis.integration_hub.connector_framework.schemas import ConnectorSyncResult


class SyncDirection(StrEnum):
    PULL = "pull"
    PUSH = "push"
    BIDIRECTIONAL = "bidirectional"


class SyncMode(StrEnum):
    FULL = "full"
    INCREMENTAL = "incremental"


@dataclass(slots=True)
class SyncJobConfig:
    """One configurable synchronization job — "toutes les
    synchronisations sont configurables" (sprint requirement)."""

    id: str
    connector_id: str
    firm_id: str
    entity_type: str
    direction: SyncDirection
    mode: SyncMode = SyncMode.INCREMENTAL
    conflict_strategy: ConflictStrategy = ConflictStrategy.REMOTE_WINS
    enabled: bool = True
    last_synced_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class SyncRunReport:
    job_id: str
    result: ConnectorSyncResult
    conflicts_pending_validation: int = 0
