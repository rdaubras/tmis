from tmis.legal_drafting.citations.engine import CitationEngine
from tmis.legal_drafting.citations.formatters import (
    FootnoteCitationFormatter,
    PlainTextCitationFormatter,
)
from tmis.legal_drafting.paragraphs.schemas import Paragraph
from tmis.legal_drafting.references.schemas import ReferenceLink, ReferenceTargetType


def _paragraph() -> Paragraph:
    return Paragraph(id="p1", section_key="facts", order=0, text="text", origin="kernel")


def _reference() -> ReferenceLink:
    return ReferenceLink(
        id="ref1",
        target_type=ReferenceTargetType.FACT,
        target_id="f1",
        label="Le contrat a été signé.",
        excerpt="Le contrat a été signé le 3 mars.",
    )


def test_build_for_paragraph_anchors_citation_to_document_section_paragraph() -> None:
    citations = CitationEngine().build_for_paragraph("doc1", "sec1", _paragraph(), [_reference()])
    assert len(citations) == 1
    citation = citations[0]
    assert citation.document_id == "doc1"
    assert citation.section_id == "sec1"
    assert citation.paragraph_id == "p1"
    assert citation.source_type == "fact"
    assert citation.source_id == "f1"


def test_build_for_paragraph_returns_empty_for_no_references() -> None:
    assert CitationEngine().build_for_paragraph("doc1", "sec1", _paragraph(), []) == []


def test_plain_text_formatter_is_compact() -> None:
    citations = CitationEngine().build_for_paragraph("doc1", "sec1", _paragraph(), [_reference()])
    formatted = PlainTextCitationFormatter().format(citations[0])
    assert "\n" not in formatted
    assert "fact" in formatted


def test_footnote_formatter_includes_excerpt_and_source_id() -> None:
    citations = CitationEngine().build_for_paragraph("doc1", "sec1", _paragraph(), [_reference()])
    formatted = FootnoteCitationFormatter().format(citations[0])
    assert "3 mars" in formatted
    assert "fact:f1" in formatted


def test_footnote_formatter_truncates_long_excerpts() -> None:
    reference = ReferenceLink(
        id="ref1", target_type=ReferenceTargetType.FACT, target_id="f1",
        label="label", excerpt="x" * 500,
    )
    citations = CitationEngine().build_for_paragraph("doc1", "sec1", _paragraph(), [reference])
    formatted = FootnoteCitationFormatter().format(citations[0])
    assert "…" in formatted
