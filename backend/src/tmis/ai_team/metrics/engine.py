from tmis.ai_team.metrics.schemas import AgentRunMetric, MissionMetricsSummary


class MetricsCollector:
    """Collects the metrics the sprint requires (see
    docs/55-guide-coordinateur.md — Métriques): time and cost per
    agent, estimated quality, consensus rate, revision count, human
    validation count. In-memory, append-only — a natural candidate to
    later feed `tmis.platform.metrics.MetricsRegistry` (Sprint 10) for
    a unified Prometheus view, without changing what's recorded here."""

    def __init__(self) -> None:
        self._agent_runs: list[AgentRunMetric] = []
        self._consensus_checks: dict[str, int] = {}
        self._consensus_resolved: dict[str, int] = {}
        self._revisions: dict[str, int] = {}
        self._human_validations: dict[str, int] = {}

    def record_agent_run(
        self,
        mission_id: str,
        sub_task_id: str,
        agent_id: str,
        duration_seconds: float,
        cost_usd: float,
        quality_score: float,
    ) -> None:
        self._agent_runs.append(
            AgentRunMetric(
                mission_id=mission_id,
                sub_task_id=sub_task_id,
                agent_id=agent_id,
                duration_seconds=duration_seconds,
                cost_usd=cost_usd,
                quality_score=quality_score,
            )
        )

    def record_consensus(self, mission_id: str, resolved: bool) -> None:
        self._consensus_checks[mission_id] = self._consensus_checks.get(mission_id, 0) + 1
        if resolved:
            self._consensus_resolved[mission_id] = self._consensus_resolved.get(mission_id, 0) + 1

    def record_revision(self, mission_id: str) -> None:
        self._revisions[mission_id] = self._revisions.get(mission_id, 0) + 1

    def record_human_validation(self, mission_id: str) -> None:
        self._human_validations[mission_id] = self._human_validations.get(mission_id, 0) + 1

    def agent_runs_for_mission(self, mission_id: str) -> list[AgentRunMetric]:
        return [m for m in self._agent_runs if m.mission_id == mission_id]

    def all_agent_runs(self) -> list[AgentRunMetric]:
        return list(self._agent_runs)

    def summary_for_mission(self, mission_id: str) -> MissionMetricsSummary:
        runs = self.agent_runs_for_mission(mission_id)
        return MissionMetricsSummary(
            mission_id=mission_id,
            total_cost_usd=sum(r.cost_usd for r in runs),
            total_duration_seconds=sum(r.duration_seconds for r in runs),
            agent_runs=len(runs),
            consensus_checks=self._consensus_checks.get(mission_id, 0),
            consensus_resolved=self._consensus_resolved.get(mission_id, 0),
            revision_count=self._revisions.get(mission_id, 0),
            human_validation_count=self._human_validations.get(mission_id, 0),
        )
