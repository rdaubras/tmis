from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class AgentRunMetric:
    """One agent execution's measured cost/time/quality (see
    docs/49-guide-supervision.md and docs/55-guide-coordinateur.md —
    Métriques). Quality is the agent's registered `quality_score` at
    run time — a proxy, not a measurement of the actual output, until
    a real evaluation model is wired in (see `tmis.ai_team.evaluation`
    for mission-level scoring, which does look at the actual output)."""

    mission_id: str
    sub_task_id: str
    agent_id: str
    duration_seconds: float
    cost_usd: float
    quality_score: float
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class MissionMetricsSummary:
    mission_id: str
    total_cost_usd: float
    total_duration_seconds: float
    agent_runs: int
    consensus_checks: int
    consensus_resolved: int
    revision_count: int
    human_validation_count: int

    @property
    def consensus_rate(self) -> float:
        if self.consensus_checks == 0:
            return 1.0
        return self.consensus_resolved / self.consensus_checks
