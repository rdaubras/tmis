from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory
from tmis.legal_copilot_framework.metrics.schemas import CopilotMetricsSnapshot


def _name(copilot_id: str, suffix: str) -> str:
    return f"copilot.{copilot_id}.{suffix}"


class CopilotMetricsEngine:
    """Composes `cloud_operations.metrics.MetricsEngine` (Sprint 21)
    exclusively — no second metrics store. Every recorded sample is
    named `copilot.{copilot_id}.{dimension}` under one of the five
    `MetricCategory` members this sprint adds, so
    `GET /cloud-operations/metrics/{category}` already exposes them
    without any new endpoint."""

    def __init__(self, metrics: MetricsEngine) -> None:
        self._metrics = metrics

    def record_usage(self, copilot_id: str, firm_id: str | None = None) -> None:
        self._metrics.record(
            MetricCategory.COPILOT_USAGE, _name(copilot_id, "usage"), 1.0, firm_id=firm_id
        )

    def record_cost(self, copilot_id: str, cost_usd: float, firm_id: str | None = None) -> None:
        self._metrics.record(
            MetricCategory.AI_COST, _name(copilot_id, "cost"), cost_usd, firm_id=firm_id
        )

    def record_response_time(
        self, copilot_id: str, duration_ms: float, firm_id: str | None = None
    ) -> None:
        self._metrics.record(
            MetricCategory.RESPONSE_TIME,
            _name(copilot_id, "response_time"),
            duration_ms,
            firm_id=firm_id,
        )

    def record_validation(
        self, copilot_id: str, approved: bool, firm_id: str | None = None
    ) -> None:
        self._metrics.record(
            MetricCategory.VALIDATION_RATE,
            _name(copilot_id, "validation"),
            1.0 if approved else 0.0,
            firm_id=firm_id,
        )

    def record_pack_reuse(self, copilot_id: str, firm_id: str | None = None) -> None:
        self._metrics.record(
            MetricCategory.PACK_REUSE, _name(copilot_id, "pack_reuse"), 1.0, firm_id=firm_id
        )

    def record_satisfaction(
        self, copilot_id: str, score: float, firm_id: str | None = None
    ) -> None:
        """Not called automatically anywhere — no user feedback UI
        exists yet. The model is prepared, not the data source."""
        self._metrics.record(
            MetricCategory.SATISFACTION, _name(copilot_id, "satisfaction"), score, firm_id=firm_id
        )

    def _events(
        self, copilot_id: str, category: MetricCategory, suffix: str, firm_id: str | None
    ) -> list[float]:
        history = self._metrics.history_for_category(category, firm_id)
        name = _name(copilot_id, suffix)
        return [e.value for e in history if e.name == name]

    def snapshot(self, copilot_id: str, firm_id: str | None = None) -> CopilotMetricsSnapshot:
        usage_events = self._events(copilot_id, MetricCategory.COPILOT_USAGE, "usage", firm_id)
        cost_events = self._events(copilot_id, MetricCategory.AI_COST, "cost", firm_id)
        response_events = self._events(
            copilot_id, MetricCategory.RESPONSE_TIME, "response_time", firm_id
        )
        validation_events = self._events(
            copilot_id, MetricCategory.VALIDATION_RATE, "validation", firm_id
        )
        pack_reuse_events = self._events(
            copilot_id, MetricCategory.PACK_REUSE, "pack_reuse", firm_id
        )
        satisfaction_events = self._events(
            copilot_id, MetricCategory.SATISFACTION, "satisfaction", firm_id
        )

        return CopilotMetricsSnapshot(
            copilot_id=copilot_id,
            usage_count=len(usage_events),
            total_ai_cost_usd=sum(cost_events),
            avg_response_time_ms=(
                sum(response_events) / len(response_events) if response_events else 0.0
            ),
            validation_rate=(
                sum(validation_events) / len(validation_events) if validation_events else 0.0
            ),
            pack_reuse_count=len(pack_reuse_events),
            satisfaction_score=(
                sum(satisfaction_events) / len(satisfaction_events)
                if satisfaction_events
                else None
            ),
        )
