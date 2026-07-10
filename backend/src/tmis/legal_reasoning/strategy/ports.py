from typing import Protocol

from tmis.legal_reasoning.arguments.schemas import Argument
from tmis.legal_reasoning.confidence.schemas import ConfidenceScore
from tmis.legal_reasoning.conflicts.schemas import Conflict
from tmis.legal_reasoning.counter_arguments.schemas import CounterArgument
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis
from tmis.legal_reasoning.strategy.schemas import StrategyOption


class StrategyEnginePort(Protocol):
    """Port implemented by every interchangeable strategy proposer."""

    def propose(
        self,
        hypotheses: list[Hypothesis],
        arguments: list[Argument],
        counter_arguments: list[CounterArgument],
        conflicts: list[Conflict],
        confidence_scores: dict[str, ConfidenceScore],
    ) -> list[StrategyOption]: ...
