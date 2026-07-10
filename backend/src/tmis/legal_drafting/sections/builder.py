import uuid

from tmis.case_intelligence.facts.schemas import Fact
from tmis.legal_drafting.paragraphs.ports import ParagraphEnginePort
from tmis.legal_drafting.sections.schemas import Section
from tmis.legal_drafting.style.schemas import StyleProfile
from tmis.legal_drafting.templates.schemas import TemplateSection
from tmis.legal_reasoning.reasoner.schemas import ReasoningSession
from tmis.legal_research.search.schemas import ResearchResult


class DocumentBuilder:
    """Implements `DocumentBuilderPort`: assembles sections in template
    order, each independently regenerable without rebuilding the rest of
    the document (see docs/28-legal-drafting.md — Document Builder).

    `depends_on` is informational at this stage (Sprint 7 always builds
    sections in template order, which already respects every
    dependency) — it exists so a future planner can parallelize
    independent sections or validate a custom section order without
    `DocumentBuilder` itself changing.
    """

    def __init__(self, paragraph_engine: ParagraphEnginePort) -> None:
        self._paragraph_engine = paragraph_engine

    async def build_sections(
        self,
        template_sections: list[TemplateSection],
        *,
        facts: list[Fact],
        research_results: list[ResearchResult],
        reasoning_session: ReasoningSession | None,
        style_profile: StyleProfile,
        variables: dict[str, str],
    ) -> list[Section]:
        ordered = sorted(template_sections, key=lambda s: s.order)
        return [
            await self._build_section(
                template_section,
                facts=facts,
                research_results=research_results,
                reasoning_session=reasoning_session,
                style_profile=style_profile,
                variables=variables,
            )
            for template_section in ordered
        ]

    async def regenerate_section(
        self,
        template_section: TemplateSection,
        *,
        facts: list[Fact],
        research_results: list[ResearchResult],
        reasoning_session: ReasoningSession | None,
        style_profile: StyleProfile,
        variables: dict[str, str],
    ) -> Section:
        return await self._build_section(
            template_section,
            facts=facts,
            research_results=research_results,
            reasoning_session=reasoning_session,
            style_profile=style_profile,
            variables=variables,
        )

    async def _build_section(
        self,
        template_section: TemplateSection,
        *,
        facts: list[Fact],
        research_results: list[ResearchResult],
        reasoning_session: ReasoningSession | None,
        style_profile: StyleProfile,
        variables: dict[str, str],
    ) -> Section:
        paragraphs = await self._paragraph_engine.generate(
            template_section,
            facts=facts,
            research_results=research_results,
            reasoning_session=reasoning_session,
            style_profile=style_profile,
            variables=variables,
        )
        return Section(
            id=str(uuid.uuid4()),
            key=template_section.key,
            title=template_section.title,
            order=template_section.order,
            paragraphs=paragraphs,
            depends_on=template_section.depends_on,
        )
