from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ConfidenceWeights:
    """Configurable weights for the Confidence Engine (see
    docs/27-guide-scores-confiance.md). Extensible on purpose: a new
    factor is added here and in `ConfigurableConfidenceEngine.score()`
    without touching any caller."""

    argument_support: float = 0.40
    evidence_reliability: float = 0.35
    absence_of_counter_arguments: float = 0.25

    def normalized(self) -> "ConfidenceWeights":
        total = (
            self.argument_support + self.evidence_reliability + self.absence_of_counter_arguments
        )
        if total <= 0:
            return ConfidenceWeights(1 / 3, 1 / 3, 1 / 3)
        return ConfidenceWeights(
            argument_support=self.argument_support / total,
            evidence_reliability=self.evidence_reliability / total,
            absence_of_counter_arguments=self.absence_of_counter_arguments / total,
        )


@dataclass(frozen=True, slots=True)
class ConfidenceScore:
    """A hypothesis' confidence, always explained (see
    docs/25-legal-reasoning.md — Confidence Engine)."""

    hypothesis_id: str
    value: float
    explanation: str
    factors: dict[str, float] = field(default_factory=dict)
