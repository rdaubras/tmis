from typing import Protocol

from tmis.legal_reasoning.arguments.schemas import Argument
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis
from tmis.legal_research.search.schemas import ResearchResult


class ArgumentEnginePort(Protocol):
    """Port implemented by every interchangeable argument builder."""

    def build(
        self, hypotheses: list[Hypothesis], research_results: list[ResearchResult]
    ) -> list[Argument]: ...
