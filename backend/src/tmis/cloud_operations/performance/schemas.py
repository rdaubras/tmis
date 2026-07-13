from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class PerformanceSnapshot:
    """Production performance over a window of `RESPONSE_TIME`/
    `THROUGHPUT` samples — distinct in scope from `platform.
    performance.benchmark.benchmark()` (Sprint 10, a micro-benchmark
    helper you call in a test/script), which this module composes
    for the micro-benchmarking use case rather than duplicating; this
    snapshot is about what production traffic actually did, not a
    synthetic timed loop."""

    firm_id: str | None
    response_time_avg_ms: float
    response_time_p95_ms: float
    throughput_total: float
    sample_count: int
    computed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
