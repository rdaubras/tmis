from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class NodeStatus(StrEnum):
    HEALTHY = "healthy"
    SUSPECT = "suspect"
    DOWN = "down"


@dataclass(slots=True)
class NodeHeartbeat:
    node_id: str
    last_heartbeat_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class ReplicationStatus:
    replica_id: str
    lag_seconds: float
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
