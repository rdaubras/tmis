from tmis.case_intelligence.facts.schemas import Fact
from tmis.legal_drafting.paragraphs.schemas import Paragraph
from tmis.legal_drafting.references.resolver import HeuristicReferenceResolver
from tmis.legal_drafting.references.schemas import ReferenceTargetType
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis
from tmis.legal_reasoning.reasoner.schemas import ReasoningSession
from tmis.legal_research.search.schemas import ResearchResult


def _paragraph(**overrides: object) -> Paragraph:
    defaults: dict[str, object] = dict(
        id="p1", section_key="facts", order=0, text="text", origin="kernel",
    )
    defaults.update(overrides)
    return Paragraph(**defaults)  # type: ignore[arg-type]


def test_resolve_links_facts() -> None:
    fact = Fact(id="f1", description="Le contrat a été signé.", confidence=0.8)
    paragraph = _paragraph(fact_ids=("f1",))

    links = HeuristicReferenceResolver().resolve(
        paragraph, facts=[fact], research_results=[], reasoning_session=None
    )

    assert len(links) == 1
    assert links[0].target_type == ReferenceTargetType.FACT
    assert links[0].target_id == "f1"


def test_resolve_links_research_results() -> None:
    result = ResearchResult(
        id="r1", title="Code civil", excerpt="excerpt", connector="codes",
        document_type="code", reference="1240", date=None,
    )
    paragraph = _paragraph(reference_ids=("r1",))

    links = HeuristicReferenceResolver().resolve(
        paragraph, facts=[], research_results=[result], reasoning_session=None
    )

    assert len(links) == 1
    assert links[0].target_type == ReferenceTargetType.RESEARCH_RESULT
    assert links[0].label == "Code civil"


def test_resolve_links_hypotheses_from_reasoning_session() -> None:
    hypothesis = Hypothesis(id="h1", description="Hypothèse test")
    session = ReasoningSession(id="s1", question="q", case_id=None, hypotheses=[hypothesis])
    paragraph = _paragraph(hypothesis_ids=("h1",))

    links = HeuristicReferenceResolver().resolve(
        paragraph, facts=[], research_results=[], reasoning_session=session
    )

    assert len(links) == 1
    assert links[0].target_type == ReferenceTargetType.HYPOTHESIS


def test_resolve_ignores_unknown_ids() -> None:
    paragraph = _paragraph(fact_ids=("unknown",))
    links = HeuristicReferenceResolver().resolve(
        paragraph, facts=[], research_results=[], reasoning_session=None
    )
    assert links == []


def test_resolve_returns_empty_for_ungrounded_paragraph() -> None:
    paragraph = _paragraph()
    links = HeuristicReferenceResolver().resolve(
        paragraph, facts=[], research_results=[], reasoning_session=None
    )
    assert links == []
