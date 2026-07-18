from tmis.ai_team.evaluation.schemas import MissionEvaluation
from tmis.ai_team.metrics.schemas import MissionMetricsSummary


class MissionQualityScorer:
    """Scores a completed mission (see docs/55-guide-coordinateur.md —
    Evaluation): the average registered quality of the agents that ran,
    weighted down by disagreement (`consensus_rate`) and by how many
    revisions the mission needed — a mission that took three human
    interventions to converge is not as strong a result as one that
    succeeded first try, even if the final text looks the same."""

    def evaluate_mission(
        self, mission_id: str, average_agent_quality: float, metrics: MissionMetricsSummary
    ) -> MissionEvaluation:
        revision_penalty = min(0.3, metrics.revision_count * 0.1)
        score = max(0.0, average_agent_quality * metrics.consensus_rate - revision_penalty)

        notes: list[str] = []
        if metrics.revision_count > 0:
            notes.append(f"{metrics.revision_count} révision(s) demandée(s) par un humain.")
        if metrics.consensus_rate < 1.0:
            notes.append("Désaccord(s) persistant(s) entre agents détecté(s).")
        if metrics.human_validation_count == 0:
            notes.append("Aucune validation humaine enregistrée à ce stade.")

        return MissionEvaluation(
            mission_id=mission_id, overall_quality_score=score, notes=tuple(notes)
        )
