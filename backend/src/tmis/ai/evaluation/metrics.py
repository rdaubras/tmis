from dataclasses import dataclass, field
from datetime import UTC, datetime

_COST_PER_1K_TOKENS_USD: dict[str, float] = {
    "openai": 0.005,
    "anthropic": 0.006,
    "mistral": 0.002,
    "local": 0.0,
}
_DEFAULT_COST_PER_1K_TOKENS_USD = 0.005


def estimate_cost(provider: str, token_count: int) -> float:
    rate = _COST_PER_1K_TOKENS_USD.get(provider, _DEFAULT_COST_PER_1K_TOKENS_USD)
    return round((token_count / 1000) * rate, 6)


@dataclass(frozen=True, slots=True)
class EvaluationMetrics:
    """Recorded for every model call mediated by `TMISKernel.complete`."""

    provider: str
    model: str
    latency_ms: float
    token_count: int
    estimated_cost_usd: float
    confidence_score: float
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
