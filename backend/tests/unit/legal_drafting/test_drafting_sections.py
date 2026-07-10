import pytest

from tmis.ai.schemas.provider import ModelResponse
from tmis.legal_drafting.sections.builder import DocumentBuilder
from tmis.legal_drafting.style.engine import StyleEngine
from tmis.legal_drafting.style.schemas import StyleProfile
from tmis.legal_drafting.templates.schemas import SectionRole, TemplateSection


class _FakeKernel:
    async def complete(self, prompt: str) -> ModelResponse:
        return ModelResponse(text=f"[genere] {prompt[:10]}", provider="fake", model="fake")


_PROFILE = StyleProfile(id="p", firm_name="F")


def _paragraph_engine():
    from tmis.legal_drafting.paragraphs.engine import HeuristicParagraphEngine

    return HeuristicParagraphEngine(_FakeKernel(), StyleEngine())


@pytest.mark.asyncio
async def test_build_sections_respects_template_order() -> None:
    template_sections = [
        TemplateSection(key="signature", role=SectionRole.SIGNATURE, title="Signature", order=2),
        TemplateSection(key="header", role=SectionRole.HEADER, title="En-tête", order=0),
        TemplateSection(key="context", role=SectionRole.CONTEXT, title="Contexte", order=1),
    ]
    builder = DocumentBuilder(_paragraph_engine())

    sections = await builder.build_sections(
        template_sections, facts=[], research_results=[], reasoning_session=None,
        style_profile=_PROFILE, variables={},
    )

    assert [s.key for s in sections] == ["header", "context", "signature"]


@pytest.mark.asyncio
async def test_build_sections_carries_over_depends_on() -> None:
    template_section = TemplateSection(
        key="legal_discussion", role=SectionRole.LEGAL_DISCUSSION, title="Discussion",
        order=0, depends_on=("facts",),
    )
    builder = DocumentBuilder(_paragraph_engine())

    sections = await builder.build_sections(
        [template_section], facts=[], research_results=[], reasoning_session=None,
        style_profile=_PROFILE, variables={},
    )

    assert sections[0].depends_on == ("facts",)


@pytest.mark.asyncio
async def test_regenerate_section_returns_a_freshly_built_section() -> None:
    template_section = TemplateSection(key="facts", role=SectionRole.FACTS, title="Faits", order=0)
    builder = DocumentBuilder(_paragraph_engine())

    section = await builder.regenerate_section(
        template_section, facts=[], research_results=[], reasoning_session=None,
        style_profile=_PROFILE, variables={},
    )

    assert section.key == "facts"
    assert len(section.paragraphs) == 1
