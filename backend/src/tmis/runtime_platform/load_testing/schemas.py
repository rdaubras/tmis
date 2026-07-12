from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import IntEnum


class LoadTestPreset(IntEnum):
    """The three concurrency levels the sprint asks for ("100, 1 000,
    10 000 utilisateurs")."""

    SMALL = 100
    MEDIUM = 1_000
    LARGE = 10_000


@dataclass(frozen=True, slots=True)
class LoadTestReport:
    concurrent_users: int
    total_requests: int
    success_count: int
    error_count: int
    avg_latency_ms: float
    p95_latency_ms: float
    throughput_rps: float
    duration_seconds: float
    executed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
