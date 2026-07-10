from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class HealthStatus(str, Enum):
    UP = "up"
    DEGRADED = "degraded"
    DOWN = "down"


@dataclass(frozen=True, slots=True)
class ComponentHealth:
    """The health of one dependency (see docs/49-guide-supervision.md
    — Health Checks): database, cache, storage, AI Kernel, event bus,
    queue, connectors — the seven the sprint brief names."""

    name: str
    status: HealthStatus
    detail: str = ""
    latency_ms: float = 0.0


@dataclass(frozen=True, slots=True)
class SystemHealth:
    status: HealthStatus
    components: list[ComponentHealth] = field(default_factory=list)
    checked_at: datetime = field(default_factory=lambda: datetime.now(UTC))
