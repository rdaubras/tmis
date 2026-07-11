from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class MissionEvaluation:
    """A mission-level quality score (see docs/55-guide-coordinateur.md
    — Evaluation), distinct from `tmis.ai_team.metrics`: metrics
    measure *what happened* (time, cost, counts); this evaluates *how
    good the result was*, combining agent quality scores with how well
    the team agreed."""

    mission_id: str
    overall_quality_score: float
    notes: tuple[str, ...] = field(default_factory=tuple)
