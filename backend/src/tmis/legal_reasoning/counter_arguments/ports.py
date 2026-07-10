from typing import Protocol

from tmis.case_intelligence.facts.schemas import Fact
from tmis.legal_reasoning.arguments.schemas import Argument
from tmis.legal_reasoning.counter_arguments.schemas import CounterArgument
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis
from tmis.legal_research.search.schemas import ResearchResult


class CounterArgumentEnginePort(Protocol):
    """Port implemented by every interchangeable counter-argument finder."""

    def build(
        self,
        arguments: list[Argument],
        hypotheses: list[Hypothesis],
        facts: list[Fact],
        research_results: list[ResearchResult],
    ) -> list[CounterArgument]: ...
