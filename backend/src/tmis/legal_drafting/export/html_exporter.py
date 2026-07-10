import html

from tmis.legal_drafting.citations.formatters import FootnoteCitationFormatter
from tmis.legal_drafting.documents.schemas import Document
from tmis.legal_drafting.export.schemas import ExportFormat, ExportResult

_DISCLAIMER = (
    "Document généré par TMIS — brouillon non validé, à relire et valider par un avocat."
)


class HtmlExporter:
    """Implements `ExporterPort`: renders a self-contained HTML document
    preserving section structure and attaching every citation as a
    footnote (see docs/32-guide-exports.md)."""

    def export(self, document: Document) -> ExportResult:
        formatter = FootnoteCitationFormatter()
        citations_by_paragraph: dict[str, list[str]] = {}
        for citation in document.citations:
            citations_by_paragraph.setdefault(citation.paragraph_id, []).append(
                formatter.format(citation)
            )

        parts = [
            "<!doctype html>",
            "<html><head><meta charset=\"utf-8\">",
            f"<title>{html.escape(document.title)}</title></head><body>",
            f"<p><em>{html.escape(_DISCLAIMER)}</em></p>",
            f"<h1>{html.escape(document.title)}</h1>",
        ]
        for section in document.sections:
            parts.append(f"<h2>{html.escape(section.title)}</h2>")
            for paragraph in section.paragraphs:
                parts.append(f"<p>{html.escape(paragraph.text)}</p>")
                for formatted in citations_by_paragraph.get(paragraph.id, []):
                    escaped = html.escape(formatted)
                    parts.append(f'<p class="citation"><small>{escaped}</small></p>')
        parts.append("</body></html>")

        content = "\n".join(parts).encode("utf-8")
        return ExportResult(
            format=ExportFormat.HTML,
            filename=f"{document.id}.html",
            content=content,
            media_type="text/html",
        )
