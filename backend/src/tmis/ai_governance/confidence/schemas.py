from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class GovernanceConfidenceWeights:
    """The sprint's confidence decomposition: qualité des sources,
    cohérence du raisonnement, validations humaines, consensus
    multi-agents, stabilité des modèles. Extensible on purpose — a new
    factor is added here and in `GovernanceConfidenceEngine.score()`
    without touching any caller (same pattern as
    `tmis.legal_reasoning.confidence.ConfidenceWeights`)."""

    source_quality: float = 0.25
    reasoning_coherence: float = 0.25
    human_validation: float = 0.20
    multi_agent_consensus: float = 0.15
    model_stability: float = 0.15

    def normalized(self) -> "GovernanceConfidenceWeights":
        total = (
            self.source_quality
            + self.reasoning_coherence
            + self.human_validation
            + self.multi_agent_consensus
            + self.model_stability
        )
        if total <= 0:
            return GovernanceConfidenceWeights(0.2, 0.2, 0.2, 0.2, 0.2)
        return GovernanceConfidenceWeights(
            source_quality=self.source_quality / total,
            reasoning_coherence=self.reasoning_coherence / total,
            human_validation=self.human_validation / total,
            multi_agent_consensus=self.multi_agent_consensus / total,
            model_stability=self.model_stability / total,
        )


@dataclass(frozen=True, slots=True)
class GovernanceConfidenceScore:
    """A production's confidence, always explained and always
    decomposable — "le détail du calcul doit être consultable"
    (sprint requirement)."""

    production_id: str
    value: float
    explanation: str
    factors: dict[str, float] = field(default_factory=dict)
