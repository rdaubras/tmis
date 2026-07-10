from tmis.legal_research.citations.ports import CitationFormatterPort
from tmis.legal_research.citations.schemas import ResearchCitation
from tmis.legal_research.search.schemas import ResearchResult


class CitationEngine:
    """Builds a traceable `ResearchCitation` from every `ResearchResult`
    and formats it through an interchangeable `CitationFormatterPort`
    (see docs/24-guide-citation-system.md)."""

    def build(self, result: ResearchResult) -> ResearchCitation:
        return ResearchCitation(
            source_id=result.id,
            title=result.title,
            date=result.date,
            document_type=result.document_type,
            reference=result.reference,
            excerpt=result.excerpt,
        )

    def format(self, citation: ResearchCitation, formatter: CitationFormatterPort) -> str:
        return formatter.format(citation)
