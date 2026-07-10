import io

import pypdf

from tmis.legal_drafting.documents.schemas import Document
from tmis.legal_drafting.export.pdf_exporter import PdfExporter
from tmis.legal_drafting.export.pdf_writer import build_minimal_pdf
from tmis.legal_drafting.export.schemas import ExportFormat
from tmis.legal_drafting.paragraphs.schemas import Paragraph
from tmis.legal_drafting.sections.schemas import Section
from tmis.legal_drafting.templates.schemas import DocumentType


def _document() -> Document:
    paragraph = Paragraph(
        id="p1", section_key="facts", order=0, text="Le contrat a ete rompu.", origin="kernel",
    )
    section = Section(id="s1", key="facts", title="Faits", order=0, paragraphs=[paragraph])
    return Document(
        id="doc1", template_id="consultation:v1", document_type=DocumentType.CONSULTATION,
        case_id=None, title="Consultation Test", sections=[section],
    )


def test_build_minimal_pdf_is_parseable_by_pypdf() -> None:
    content = build_minimal_pdf(["Ligne un", "Ligne deux"])
    reader = pypdf.PdfReader(io.BytesIO(content))
    assert len(reader.pages) == 1
    text = reader.pages[0].extract_text()
    assert "Ligne un" in text
    assert "Ligne deux" in text


def test_build_minimal_pdf_paginates_long_content() -> None:
    lines = [f"Ligne {i}" for i in range(120)]
    content = build_minimal_pdf(lines, lines_per_page=45)
    reader = pypdf.PdfReader(io.BytesIO(content))
    assert len(reader.pages) == 3


def test_build_minimal_pdf_handles_empty_input() -> None:
    content = build_minimal_pdf([])
    reader = pypdf.PdfReader(io.BytesIO(content))
    assert len(reader.pages) == 1


def test_export_returns_pdf_media_type() -> None:
    result = PdfExporter().export(_document())
    assert result.format == ExportFormat.PDF
    assert result.media_type == "application/pdf"


def test_export_pdf_contains_document_content() -> None:
    result = PdfExporter().export(_document())
    reader = pypdf.PdfReader(io.BytesIO(result.content))
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert "Consultation Test" in text
    assert "Faits" in text
    assert "rompu" in text
