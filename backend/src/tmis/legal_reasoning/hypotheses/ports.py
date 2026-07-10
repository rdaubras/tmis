from typing import Protocol

from tmis.case_intelligence.facts.schemas import Fact
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis
from tmis.legal_research.search.schemas import ResearchResult


class HypothesisEnginePort(Protocol):
    """Port implemented by every interchangeable hypothesis generator."""

    def generate(
        self, question: str, facts: list[Fact], research_results: list[ResearchResult]
    ) -> list[Hypothesis]: ...
