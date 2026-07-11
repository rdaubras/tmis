from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class BenchmarkRun:
    """One measured run of a model, per the sprint's "BENCHMARK
    ENGINE" spec: qualité, coût, latence, hallucinations, stabilité,
    consommation de tokens."""

    model_name: str
    quality_score: float
    cost_usd: float
    latency_ms: float
    hallucination_flags: int
    token_count: int
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
