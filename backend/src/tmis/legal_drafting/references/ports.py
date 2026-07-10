from typing import Protocol

from tmis.case_intelligence.facts.schemas import Fact
from tmis.legal_drafting.paragraphs.schemas import Paragraph
from tmis.legal_drafting.references.schemas import ReferenceLink
from tmis.legal_reasoning.reasoner.schemas import ReasoningSession
from tmis.legal_research.search.schemas import ResearchResult


class ReferenceResolverPort(Protocol):
    """Port implemented by every interchangeable reference resolver.

    Takes the individual upstream pieces (facts, research results, a
    reasoning session) rather than a full `DraftingContext`, so this
    stays a leaf module `documents.orchestrator` depends on — never the
    other way around (same pattern as
    `tmis.legal_reasoning.explanations`/`decision_graph`, Sprint 6).
    """

    def resolve(
        self,
        paragraph: Paragraph,
        *,
        facts: list[Fact],
        research_results: list[ResearchResult],
        reasoning_session: ReasoningSession | None,
    ) -> list[ReferenceLink]: ...
