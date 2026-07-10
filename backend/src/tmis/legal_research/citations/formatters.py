from tmis.legal_research.citations.schemas import ResearchCitation

_EXCERPT_PREVIEW_CHARS = 160


class PlainTextCitationFormatter:
    """Implements `CitationFormatterPort`: a compact single-line format,
    suitable for chat/agent output (see docs/24-guide-citation-system.md)."""

    def format(self, citation: ResearchCitation) -> str:
        date_part = f", {citation.date}" if citation.date else ""
        return f"{citation.title} ({citation.reference}{date_part})"


class FootnoteCitationFormatter:
    """Implements `CitationFormatterPort`: a footnote-style format with
    the excerpt used, suitable for generated documents."""

    def format(self, citation: ResearchCitation) -> str:
        date_part = f", {citation.date}" if citation.date else ""
        excerpt = citation.excerpt[:_EXCERPT_PREVIEW_CHARS]
        if len(citation.excerpt) > _EXCERPT_PREVIEW_CHARS:
            excerpt += "…"
        return (
            f"{citation.title}, {citation.document_type}, {citation.reference}"
            f"{date_part} — « {excerpt} » [source: {citation.source_id}]"
        )
