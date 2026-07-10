from tmis.legal_research.citations.engine import CitationEngine
from tmis.legal_research.citations.formatters import (
    FootnoteCitationFormatter,
    PlainTextCitationFormatter,
)
from tmis.legal_research.search.schemas import ResearchResult


def _result() -> ResearchResult:
    return ResearchResult(
        id="civ-1240",
        title="Code civil, article 1240",
        excerpt="Tout fait quelconque de l'homme...",
        connector="codes",
        document_type="code",
        reference="1240",
        date="1804-01-01",
    )


def test_build_keeps_all_six_traceability_fields() -> None:
    citation = CitationEngine().build(_result())
    assert citation.source_id == "civ-1240"
    assert citation.title == "Code civil, article 1240"
    assert citation.date == "1804-01-01"
    assert citation.document_type == "code"
    assert citation.reference == "1240"
    assert citation.excerpt.startswith("Tout fait")


def test_plain_text_formatter_is_a_single_line() -> None:
    citation = CitationEngine().build(_result())
    formatted = PlainTextCitationFormatter().format(citation)
    assert "\n" not in formatted
    assert "1240" in formatted


def test_footnote_formatter_includes_excerpt_and_source_id() -> None:
    citation = CitationEngine().build(_result())
    formatted = FootnoteCitationFormatter().format(citation)
    assert "Tout fait" in formatted
    assert "civ-1240" in formatted


def test_footnote_formatter_truncates_long_excerpts() -> None:
    result = _result()
    result.excerpt = "x" * 500
    citation = CitationEngine().build(result)
    formatted = FootnoteCitationFormatter().format(citation)
    assert "…" in formatted


def test_engine_format_delegates_to_formatter() -> None:
    engine = CitationEngine()
    citation = engine.build(_result())
    formatter = PlainTextCitationFormatter()
    assert engine.format(citation, formatter) == formatter.format(citation)
