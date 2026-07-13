from tmis.cloud_operations.capacity.schemas import CapacityForecast
from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory


class CapacityEngine:
    """Capacity planning over `cloud_operations.metrics` history —
    never a second measurement source, only a trend projection on
    top of it."""

    def __init__(self, metrics: MetricsEngine) -> None:
        self._metrics = metrics

    def forecast(
        self, category: MetricCategory, firm_id: str | None = None, *, periods_ahead: int = 1
    ) -> CapacityForecast | None:
        history = self._metrics.history_for_category(category, firm_id)
        if len(history) < 2:
            return None
        midpoint = len(history) // 2
        first_half = history[:midpoint] or history[:1]
        second_half = history[midpoint:]
        first_avg = sum(e.value for e in first_half) / len(first_half)
        second_avg = sum(e.value for e in second_half) / len(second_half)
        growth_rate = ((second_avg - first_avg) / first_avg * 100) if first_avg else 0.0
        current_value = history[-1].value
        projected_value = current_value * ((1 + growth_rate / 100) ** periods_ahead)
        return CapacityForecast(
            category=category,
            firm_id=firm_id,
            current_value=current_value,
            growth_rate_percent=growth_rate,
            projected_value=projected_value,
            periods_ahead=periods_ahead,
        )
