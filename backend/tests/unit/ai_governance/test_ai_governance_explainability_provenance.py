from tmis.ai_governance.explainability.engine import ExplainabilityEngine
from tmis.ai_governance.explainability.schemas import IgnoredElement
from tmis.ai_governance.explainability.store import InMemoryExplainabilityStore
from tmis.ai_governance.provenance.engine import ProvenanceEngine
from tmis.ai_governance.provenance.schemas import ProvenanceGranularity, SourceType
from tmis.ai_governance.provenance.store import InMemoryProvenanceStore

FIRM = "firm-a"
PRODUCTION = "prod-1"


def _explainability_engine() -> ExplainabilityEngine:
    return ExplainabilityEngine(InMemoryExplainabilityStore())


def test_generate_produces_a_report_readable_by_a_lawyer() -> None:
    engine = _explainability_engine()

    report = engine.generate(
        FIRM,
        PRODUCTION,
        summary="Le bail peut être résilié.",
        steps_followed=("Question", "Analyse"),
        agents_involved=("Analyste documentaire",),
        models_used=("gpt-4-legal",),
        legal_references=("Code civil art. 1103",),
        documents_consulted=("Contrat de bail",),
        ignored_elements=(IgnoredElement("Clause de garantie", "Non pertinente au litige"),),
    )

    assert report.summary == "Le bail peut être résilié."
    assert report.ignored_elements[0].justification == "Non pertinente au litige"


def test_history_accumulates_every_generated_report() -> None:
    engine = _explainability_engine()
    engine.generate(FIRM, PRODUCTION, summary="v1", steps_followed=())
    engine.generate(FIRM, PRODUCTION, summary="v2", steps_followed=())

    history = engine.history(FIRM, PRODUCTION)

    assert [r.summary for r in history] == ["v1", "v2"]


def test_latest_returns_the_most_recent_report() -> None:
    engine = _explainability_engine()
    engine.generate(FIRM, PRODUCTION, summary="v1", steps_followed=())
    engine.generate(FIRM, PRODUCTION, summary="v2", steps_followed=())

    latest = engine.latest(FIRM, PRODUCTION)

    assert latest is not None
    assert latest.summary == "v2"


def test_latest_returns_none_when_nothing_generated() -> None:
    engine = _explainability_engine()

    assert engine.latest(FIRM, "unknown") is None


def _provenance_engine() -> ProvenanceEngine:
    return ProvenanceEngine(InMemoryProvenanceStore())


def test_provenance_record_captures_all_sprint_fields() -> None:
    engine = _provenance_engine()

    record = engine.record(
        FIRM,
        PRODUCTION,
        granularity=ProvenanceGranularity.PARAGRAPH,
        locator="para-3",
        excerpt="Art. 1103 impose la force obligatoire.",
        source_type=SourceType.STATUTE_ARTICLE,
        source_reference="Code civil art. 1103",
        produced_by_agent="Analyste documentaire",
        produced_by_model="gpt-4-legal",
    )

    assert record.granularity is ProvenanceGranularity.PARAGRAPH
    assert record.source_type is SourceType.STATUTE_ARTICLE
    assert record.produced_by_model == "gpt-4-legal"


def test_trace_at_granularity_filters_correctly() -> None:
    engine = _provenance_engine()
    engine.record(
        FIRM,
        PRODUCTION,
        granularity=ProvenanceGranularity.DOCUMENT,
        locator="doc-1",
        excerpt="...",
        source_type=SourceType.DOCUMENTARY_SOURCE,
        source_reference="Pièce 1",
    )
    engine.record(
        FIRM,
        PRODUCTION,
        granularity=ProvenanceGranularity.SENTENCE,
        locator="s-1",
        excerpt="...",
        source_type=SourceType.JURISPRUDENCE,
        source_reference="Cass. civ. 1re, 12 janvier 2020",
    )

    sentences = engine.trace_at_granularity(FIRM, PRODUCTION, ProvenanceGranularity.SENTENCE)

    assert len(sentences) == 1
    assert sentences[0].source_type is SourceType.JURISPRUDENCE


def test_trace_returns_every_granularity_for_a_production() -> None:
    engine = _provenance_engine()
    engine.record(
        FIRM,
        PRODUCTION,
        granularity=ProvenanceGranularity.SECTION,
        locator="sec-1",
        excerpt="...",
        source_type=SourceType.INTERNAL_DOCUMENT,
        source_reference="Note interne",
    )

    assert len(engine.trace(FIRM, PRODUCTION)) == 1
