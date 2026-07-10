import pytest

from tmis.ai.schemas.provider import ModelResponse
from tmis.case_intelligence.facts.schemas import Fact
from tmis.legal_drafting.paragraphs.engine import HeuristicParagraphEngine
from tmis.legal_drafting.style.engine import StyleEngine
from tmis.legal_drafting.style.schemas import StyleProfile
from tmis.legal_drafting.templates.schemas import SectionRole, TemplateSection
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis
from tmis.legal_reasoning.reasoner.schemas import ReasoningSession
from tmis.legal_research.search.schemas import ResearchResult


class _FakeKernel:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    async def complete(self, prompt: str) -> ModelResponse:
        self.prompts.append(prompt)
        return ModelResponse(text=f"[genere] {prompt[:20]}", provider="fake", model="fake")


_PROFILE = StyleProfile(id="p", firm_name="Cabinet Test")


def _section(role: SectionRole, key: str = "s1") -> TemplateSection:
    return TemplateSection(key=key, role=role, title="Titre", order=0)


@pytest.mark.asyncio
async def test_header_is_deterministic_without_a_kernel_call() -> None:
    kernel = _FakeKernel()
    engine = HeuristicParagraphEngine(kernel, StyleEngine())

    paragraphs = await engine.generate(
        _section(SectionRole.HEADER, "header"),
        facts=[], research_results=[], reasoning_session=None,
        style_profile=_PROFILE, variables={"firm_name": "Cabinet X", "client_name": "Dupont"},
    )

    assert len(paragraphs) == 1
    assert "Cabinet X" in paragraphs[0].text
    assert "Dupont" in paragraphs[0].text
    assert paragraphs[0].origin == "template"
    assert kernel.prompts == []


@pytest.mark.asyncio
async def test_signature_uses_style_engine_closing_formula() -> None:
    kernel = _FakeKernel()
    engine = HeuristicParagraphEngine(kernel, StyleEngine())

    paragraphs = await engine.generate(
        _section(SectionRole.SIGNATURE, "signature"),
        facts=[], research_results=[], reasoning_session=None,
        style_profile=StyleProfile(id="p", firm_name="F", tone="formal"),
        variables={"firm_name": "Cabinet X"},
    )

    assert "salutations distinguées" in paragraphs[0].text
    assert kernel.prompts == []


@pytest.mark.asyncio
async def test_facts_section_grounds_paragraph_in_fact_ids() -> None:
    kernel = _FakeKernel()
    engine = HeuristicParagraphEngine(kernel, StyleEngine())
    fact = Fact(id="f1", description="Le contrat a été rompu.", confidence=0.8)

    paragraphs = await engine.generate(
        _section(SectionRole.FACTS, "facts"),
        facts=[fact], research_results=[], reasoning_session=None,
        style_profile=_PROFILE, variables={},
    )

    assert paragraphs[0].fact_ids == ("f1",)
    assert paragraphs[0].origin == "kernel"
    assert len(kernel.prompts) == 1


@pytest.mark.asyncio
async def test_legal_discussion_grounds_paragraph_in_research_and_hypotheses() -> None:
    kernel = _FakeKernel()
    engine = HeuristicParagraphEngine(kernel, StyleEngine())
    result = ResearchResult(
        id="r1", title="Code civil", excerpt="excerpt", connector="codes",
        document_type="code", reference="1240", date=None,
    )
    hypothesis = Hypothesis(id="h1", description="Hypothèse test")
    session = ReasoningSession(id="s1", question="q", case_id=None, hypotheses=[hypothesis])

    paragraphs = await engine.generate(
        _section(SectionRole.LEGAL_DISCUSSION, "legal_discussion"),
        facts=[], research_results=[result], reasoning_session=session,
        style_profile=_PROFILE, variables={},
    )

    assert paragraphs[0].reference_ids == ("r1",)
    assert paragraphs[0].hypothesis_ids == ("h1",)


@pytest.mark.asyncio
async def test_regenerate_one_keeps_the_same_id_and_order() -> None:
    kernel = _FakeKernel()
    engine = HeuristicParagraphEngine(kernel, StyleEngine())
    section = _section(SectionRole.FACTS, "facts")
    original = (
        await engine.generate(
            section, facts=[], research_results=[], reasoning_session=None,
            style_profile=_PROFILE, variables={},
        )
    )[0]
    original.order = 3

    regenerated = await engine.regenerate_one(
        original, section, facts=[], research_results=[], reasoning_session=None,
        style_profile=_PROFILE, variables={},
    )

    assert regenerated.id == original.id
    assert regenerated.order == 3
