from typing import Protocol

from tmis.ai.schemas.provider import ModelResponse
from tmis.case_intelligence.facts.schemas import Fact
from tmis.legal_drafting.paragraphs.schemas import Paragraph
from tmis.legal_drafting.style.schemas import StyleProfile
from tmis.legal_drafting.templates.schemas import TemplateSection
from tmis.legal_reasoning.reasoner.schemas import ReasoningSession
from tmis.legal_research.search.schemas import ResearchResult


class DraftingKernelPort(Protocol):
    """The only Kernel capability the Paragraph Engine needs — see
    docs/28-legal-drafting.md: the sole model-call point of the whole
    Legal Drafting Studio."""

    async def complete(self, prompt: str) -> ModelResponse: ...


class ParagraphEnginePort(Protocol):
    """Port implemented by every interchangeable paragraph generator.

    Takes the individual upstream pieces rather than a full
    `DraftingContext`, so `paragraphs` stays a leaf module that
    `documents.orchestrator` and `sections.DocumentBuilder` depend on —
    never the other way around.
    """

    async def generate(
        self,
        template_section: TemplateSection,
        *,
        facts: list[Fact],
        research_results: list[ResearchResult],
        reasoning_session: ReasoningSession | None,
        style_profile: StyleProfile,
        variables: dict[str, str],
    ) -> list[Paragraph]: ...

    async def regenerate_one(
        self,
        paragraph: Paragraph,
        template_section: TemplateSection,
        *,
        facts: list[Fact],
        research_results: list[ResearchResult],
        reasoning_session: ReasoningSession | None,
        style_profile: StyleProfile,
        variables: dict[str, str],
    ) -> Paragraph: ...
