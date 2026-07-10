from typing import Protocol

from tmis.case_intelligence.facts.schemas import Fact
from tmis.legal_reasoning.arguments.schemas import Argument
from tmis.legal_reasoning.evidence.schemas import ReasoningEvidenceLink
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis


class EvidenceEnginePort(Protocol):
    """Port implemented by every interchangeable reasoning-evidence linker."""

    def link(
        self,
        hypotheses: list[Hypothesis],
        arguments: list[Argument],
        facts: list[Fact],
    ) -> list[ReasoningEvidenceLink]: ...
