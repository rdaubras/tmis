from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ModelPosition:
    """One model's answer to a shared prompt, submitted for
    consensus-building or fusion."""

    model_name: str
    text: str
    quality_score: float = 0.5


@dataclass(frozen=True, slots=True)
class ConsensusOutcome:
    topic: str
    positions: tuple[ModelPosition, ...]
    agreement_ratio: float
    synthesis: str
    divergences: tuple[str, ...] = field(default_factory=tuple)

    @property
    def has_persistent_divergence(self) -> bool:
        return len(self.divergences) > 0
