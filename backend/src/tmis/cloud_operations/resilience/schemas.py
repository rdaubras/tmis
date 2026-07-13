from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass(slots=True)
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout_seconds: float = 30.0


@dataclass(slots=True)
class CircuitBreakerState:
    name: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    opened_at: datetime | None = None
