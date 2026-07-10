from tmis.legal_drafting.citations.schemas import DraftCitation
from tmis.legal_drafting.documents.schemas import Document
from tmis.legal_drafting.export.html_exporter import HtmlExporter
from tmis.legal_drafting.export.schemas import ExportFormat
from tmis.legal_drafting.paragraphs.schemas import Paragraph
from tmis.legal_drafting.sections.schemas import Section
from tmis.legal_drafting.templates.schemas import DocumentType


def _document() -> Document:
    paragraph = Paragraph(
        id="p1", section_key="facts", order=0, text="Le contrat a été rompu.", origin="kernel",
    )
    section = Section(id="s1", key="facts", title="Faits", order=0, paragraphs=[paragraph])
    citation = DraftCitation(
        id="c1", document_id="doc1", section_id="s1", paragraph_id="p1",
        source_type="fact", source_id="f1", reference="Fait n°1", excerpt="excerpt",
    )
    return Document(
        id="doc1", template_id="consultation:v1", document_type=DocumentType.CONSULTATION,
        case_id=None, title="Consultation <Test> & Cie", sections=[section], citations=[citation],
    )


def test_export_returns_html_media_type() -> None:
    result = HtmlExporter().export(_document())
    assert result.format == ExportFormat.HTML
    assert result.media_type == "text/html"
    assert result.filename == "doc1.html"


def test_export_contains_section_titles_and_paragraph_text() -> None:
    result = HtmlExporter().export(_document())
    html_text = result.content.decode("utf-8")
    assert "Faits" in html_text
    assert "Le contrat a été rompu." in html_text


def test_export_escapes_html_in_title() -> None:
    result = HtmlExporter().export(_document())
    html_text = result.content.decode("utf-8")
    assert "<Test>" not in html_text
    assert "&lt;Test&gt;" in html_text


def test_export_includes_the_draft_disclaimer() -> None:
    result = HtmlExporter().export(_document())
    html_text = result.content.decode("utf-8")
    assert "brouillon" in html_text.lower()


def test_export_attaches_citation_footnote() -> None:
    result = HtmlExporter().export(_document())
    html_text = result.content.decode("utf-8")
    assert "Fait n" in html_text
