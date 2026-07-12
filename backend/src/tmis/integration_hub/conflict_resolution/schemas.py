from dataclasses import dataclass
from enum import StrEnum

from tmis.integration_hub.connector_framework.schemas import ConnectorRecord


class ConflictStrategy(StrEnum):
    LOCAL_WINS = "local_wins"
    REMOTE_WINS = "remote_wins"
    LAST_WRITE_WINS = "last_write_wins"
    HUMAN_VALIDATION = "human_validation"


@dataclass(frozen=True, slots=True)
class ConflictContext:
    connector_id: str
    firm_id: str
    entity_type: str
    external_id: str
    local_record: ConnectorRecord
    remote_record: ConnectorRecord


@dataclass(frozen=True, slots=True)
class ConflictResolution:
    resolved_record: ConnectorRecord | None
    strategy_used: ConflictStrategy
    pending_human_validation: bool = False
    detail: str = ""
