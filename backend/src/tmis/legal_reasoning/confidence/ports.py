from typing import Protocol

from tmis.legal_reasoning.arguments.schemas import Argument
from tmis.legal_reasoning.confidence.schemas import ConfidenceScore, ConfidenceWeights
from tmis.legal_reasoning.counter_arguments.schemas import CounterArgument
from tmis.legal_reasoning.evidence.schemas import ReasoningEvidenceLink
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis


class ConfidenceEnginePort(Protocol):
    """Port implemented by every interchangeable confidence engine."""

    def score(
        self,
        hypothesis: Hypothesis,
        arguments: list[Argument],
        counter_arguments: list[CounterArgument],
        evidence_links: list[ReasoningEvidenceLink],
        weights: ConfidenceWeights | None = None,
    ) -> ConfidenceScore: ...
