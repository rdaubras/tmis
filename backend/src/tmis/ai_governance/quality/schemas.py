from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GovernanceQualityBreakdown:
    """Mirrors `tmis.cabinet_knowledge.quality.QualityBreakdown`'s
    "N factors in [0, 1], averaged" pattern, scoped to one AI
    production's overall governance quality."""

    production_id: str
    explainability_completeness: float
    provenance_completeness: float
    confidence_value: float
    risk_absence: float
    human_validation_coverage: float

    @property
    def overall(self) -> float:
        return (
            self.explainability_completeness
            + self.provenance_completeness
            + self.confidence_value
            + self.risk_absence
            + self.human_validation_coverage
        ) / 5
