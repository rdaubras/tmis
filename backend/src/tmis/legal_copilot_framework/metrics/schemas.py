from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CopilotMetricsSnapshot:
    """The six metrics the sprint asks for. `satisfaction_score`
    stays `None` unless `CopilotMetricsEngine.record_satisfaction` has
    actually been called — "prévoir le modèle" (sprint requirement),
    not fabricate a value nothing currently measures."""

    copilot_id: str
    usage_count: int
    total_ai_cost_usd: float
    avg_response_time_ms: float
    validation_rate: float
    pack_reuse_count: int
    satisfaction_score: float | None
