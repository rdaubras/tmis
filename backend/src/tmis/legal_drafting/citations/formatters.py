from tmis.legal_drafting.citations.schemas import DraftCitation

_EXCERPT_PREVIEW_CHARS = 160


class PlainTextCitationFormatter:
    """Implements `CitationFormatterPort`: a compact single-line format."""

    def format(self, citation: DraftCitation) -> str:
        return f"{citation.reference} ({citation.source_type})"


class FootnoteCitationFormatter:
    """Implements `CitationFormatterPort`: a footnote-style format
    including the excerpt used, suitable for exported documents."""

    def format(self, citation: DraftCitation) -> str:
        excerpt = citation.excerpt[:_EXCERPT_PREVIEW_CHARS]
        if len(citation.excerpt) > _EXCERPT_PREVIEW_CHARS:
            excerpt += "…"
        return f"{citation.reference} — « {excerpt} » [{citation.source_type}:{citation.source_id}]"
