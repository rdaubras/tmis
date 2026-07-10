from typing import Protocol

from tmis.case_intelligence.evidence.schemas import EvidenceLink
from tmis.case_intelligence.facts.schemas import Fact


class EvidenceLinkerPort(Protocol):
    """Port implemented by every interchangeable evidence-linking engine."""

    def link(self, fact: Fact) -> list[EvidenceLink]: ...
