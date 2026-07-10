from typing import Protocol

from tmis.case_intelligence.facts.schemas import Fact
from tmis.legal_drafting.sections.schemas import Section
from tmis.legal_drafting.style.schemas import StyleProfile
from tmis.legal_drafting.templates.schemas import TemplateSection
from tmis.legal_reasoning.reasoner.schemas import ReasoningSession
from tmis.legal_research.search.schemas import ResearchResult


class DocumentBuilderPort(Protocol):
    """Port implemented by every interchangeable section assembler."""

    async def build_sections(
        self,
        template_sections: list[TemplateSection],
        *,
        facts: list[Fact],
        research_results: list[ResearchResult],
        reasoning_session: ReasoningSession | None,
        style_profile: StyleProfile,
        variables: dict[str, str],
    ) -> list[Section]: ...

    async def regenerate_section(
        self,
        template_section: TemplateSection,
        *,
        facts: list[Fact],
        research_results: list[ResearchResult],
        reasoning_session: ReasoningSession | None,
        style_profile: StyleProfile,
        variables: dict[str, str],
    ) -> Section: ...
