from dataclasses import dataclass, field


@dataclass(slots=True)
class ModelQualityStats:
    """Running quality statistics for one model, per the sprint's
    "QUALITY OPTIMIZER" spec: taux d'erreur, qualité perçue, retours
    utilisateurs, stabilité du modèle."""

    model_name: str
    total_calls: int = 0
    error_count: int = 0
    feedback_scores: list[float] = field(default_factory=list)

    @property
    def error_rate(self) -> float:
        return self.error_count / self.total_calls if self.total_calls else 0.0

    @property
    def average_feedback(self) -> float:
        if not self.feedback_scores:
            return 0.5
        return sum(self.feedback_scores) / len(self.feedback_scores)

    @property
    def stability_score(self) -> float:
        return max(0.0, 1.0 - self.error_rate)
