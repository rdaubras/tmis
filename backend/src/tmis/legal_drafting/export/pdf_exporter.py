from tmis.legal_drafting.citations.formatters import PlainTextCitationFormatter
from tmis.legal_drafting.documents.schemas import Document
from tmis.legal_drafting.export.pdf_writer import build_minimal_pdf
from tmis.legal_drafting.export.schemas import ExportFormat, ExportResult

_DISCLAIMER = "Document genere par TMIS - brouillon non valide, a relire et valider par un avocat."


class PdfExporter:
    """Implements `ExporterPort` via a minimal hand-rolled PDF writer
    (see `pdf_writer.py` and docs/32-guide-exports.md): preserves
    section titles and paragraph order, with a plain-text citation line
    right after the paragraph it supports."""

    def export(self, document: Document) -> ExportResult:
        formatter = PlainTextCitationFormatter()
        citations_by_paragraph: dict[str, list[str]] = {}
        for citation in document.citations:
            citations_by_paragraph.setdefault(citation.paragraph_id, []).append(
                formatter.format(citation)
            )

        lines = [_DISCLAIMER, "", document.title, ""]
        for section in document.sections:
            lines.append(section.title)
            for paragraph in section.paragraphs:
                lines.append(paragraph.text)
                lines.extend(f"  [{c}]" for c in citations_by_paragraph.get(paragraph.id, []))
            lines.append("")

        content = build_minimal_pdf(lines)
        return ExportResult(
            format=ExportFormat.PDF,
            filename=f"{document.id}.pdf",
            content=content,
            media_type="application/pdf",
        )
