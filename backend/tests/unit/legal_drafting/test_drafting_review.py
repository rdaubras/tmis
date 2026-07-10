from tmis.legal_drafting.paragraphs.schemas import Paragraph
from tmis.legal_drafting.review.engine import HeuristicReviewEngine
from tmis.legal_drafting.review.schemas import ReviewFindingType
from tmis.legal_drafting.sections.schemas import Section
from tmis.legal_drafting.templates.schemas import SectionRole, TemplateSection
from tmis.legal_reasoning.conflicts.schemas import Conflict, ConflictType
from tmis.legal_reasoning.reasoner.schemas import ReasoningSession


def _template_section(key: str, required: bool = True) -> TemplateSection:
    return TemplateSection(
        key=key, role=SectionRole.FACTS, title="Titre", order=0, required=required
    )


def _paragraph(**overrides: object) -> Paragraph:
    defaults: dict[str, object] = dict(
        id="p1", section_key="facts", order=0, text="Un paragraphe.", origin="kernel",
    )
    defaults.update(overrides)
    return Paragraph(**defaults)  # type: ignore[arg-type]


def test_incomplete_section_flagged_when_required_section_missing() -> None:
    template_sections = [_template_section("facts")]
    findings = HeuristicReviewEngine().review([], template_sections, None)
    assert any(f.type == ReviewFindingType.INCOMPLETE_SECTION for f in findings)


def test_incomplete_section_not_flagged_when_optional() -> None:
    template_sections = [_template_section("facts", required=False)]
    findings = HeuristicReviewEngine().review([], template_sections, None)
    assert not any(f.type == ReviewFindingType.INCOMPLETE_SECTION for f in findings)


def test_unjustified_paragraph_flagged_when_no_grounding_at_all() -> None:
    section = Section(id="s1", key="facts", title="Faits", order=0, paragraphs=[_paragraph()])
    findings = HeuristicReviewEngine().review([section], [_template_section("facts")], None)
    assert any(f.type == ReviewFindingType.UNJUSTIFIED_PARAGRAPH for f in findings)


def test_missing_reference_flagged_when_grounded_but_no_research_reference() -> None:
    paragraph = _paragraph(fact_ids=("f1",))
    section = Section(id="s1", key="facts", title="Faits", order=0, paragraphs=[paragraph])
    findings = HeuristicReviewEngine().review([section], [_template_section("facts")], None)
    assert any(f.type == ReviewFindingType.MISSING_REFERENCE for f in findings)
    assert not any(f.type == ReviewFindingType.UNJUSTIFIED_PARAGRAPH for f in findings)


def test_template_and_style_engine_origins_are_exempt_from_justification_checks() -> None:
    paragraph = _paragraph(id="p2", origin="template")
    section = Section(id="s1", key="header", title="En-tête", order=0, paragraphs=[paragraph])
    findings = HeuristicReviewEngine().review([section], [_template_section("header")], None)
    assert findings == []


def test_repetition_flagged_for_identical_paragraph_text() -> None:
    p1 = _paragraph(id="p1", text="Texte identique.", reference_ids=("r1",))
    p2 = _paragraph(id="p2", text="Texte identique.", reference_ids=("r1",))
    section = Section(id="s1", key="facts", title="Faits", order=0, paragraphs=[p1, p2])
    findings = HeuristicReviewEngine().review([section], [_template_section("facts")], None)
    assert any(f.type == ReviewFindingType.REPETITION for f in findings)


def test_contradiction_flagged_when_paragraph_touches_a_disputed_fact() -> None:
    paragraph = _paragraph(fact_ids=("f1",), reference_ids=("r1",))
    section = Section(id="s1", key="facts", title="Faits", order=0, paragraphs=[paragraph])
    conflict = Conflict(
        id="c1", type=ConflictType.FACT_INCONSISTENCY, description="d", explanation="e",
        involved_ids=("f1",),
    )
    session = ReasoningSession(id="s1", question="q", case_id=None, conflicts=[conflict])

    findings = HeuristicReviewEngine().review([section], [_template_section("facts")], session)

    assert any(f.type == ReviewFindingType.CONTRADICTION for f in findings)


def test_clean_document_has_no_findings() -> None:
    paragraph = _paragraph(fact_ids=("f1",), reference_ids=("r1",))
    section = Section(id="s1", key="facts", title="Faits", order=0, paragraphs=[paragraph])
    findings = HeuristicReviewEngine().review([section], [_template_section("facts")], None)
    assert findings == []
