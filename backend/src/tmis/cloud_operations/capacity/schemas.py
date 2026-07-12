from dataclasses import dataclass, field
from datetime import UTC, datetime

from tmis.cloud_operations.metrics.schemas import MetricCategory


@dataclass(frozen=True, slots=True)
class CapacityForecast:
    """A simple linear trend forecast: the observation history for a
    category is split into two halves; the percentage change between
    the first half's average and the second half's average is the
    growth rate, compounded forward `periods_ahead` times. A
    deliberately simple, honest model — not a statistical forecasting
    library — sufficient for a "which category is trending toward its
    limit" capacity-planning signal."""

    category: MetricCategory
    firm_id: str | None
    current_value: float
    growth_rate_percent: float
    projected_value: float
    periods_ahead: int
    computed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
