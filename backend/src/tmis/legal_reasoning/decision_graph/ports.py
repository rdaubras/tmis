from typing import Protocol

from tmis.legal_reasoning.arguments.schemas import Argument
from tmis.legal_reasoning.counter_arguments.schemas import CounterArgument
from tmis.legal_reasoning.decision_graph.schemas import DecisionGraph
from tmis.legal_reasoning.evidence.schemas import ReasoningEvidenceLink
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis


class DecisionGraphBuilderPort(Protocol):
    """Port implemented by every interchangeable decision graph builder."""

    def build(
        self,
        question: str,
        hypotheses: list[Hypothesis],
        arguments: list[Argument],
        counter_arguments: list[CounterArgument],
        evidence_links: list[ReasoningEvidenceLink],
        references: list[str],
        synthesis: str,
    ) -> DecisionGraph: ...
