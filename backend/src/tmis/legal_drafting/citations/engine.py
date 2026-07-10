import uuid

from tmis.legal_drafting.citations.ports import CitationFormatterPort
from tmis.legal_drafting.citations.schemas import DraftCitation
from tmis.legal_drafting.paragraphs.schemas import Paragraph
from tmis.legal_drafting.references.schemas import ReferenceLink


class CitationEngine:
    """Builds `DraftCitation`s anchored to a document/section/paragraph
    from the `ReferenceLink`s a paragraph resolved to (see
    docs/28-legal-drafting.md — Citation Engine)."""

    def build_for_paragraph(
        self,
        document_id: str,
        section_id: str,
        paragraph: Paragraph,
        references: list[ReferenceLink],
    ) -> list[DraftCitation]:
        return [
            DraftCitation(
                id=str(uuid.uuid4()),
                document_id=document_id,
                section_id=section_id,
                paragraph_id=paragraph.id,
                source_type=reference.target_type.value,
                source_id=reference.target_id,
                reference=reference.label,
                excerpt=reference.excerpt,
            )
            for reference in references
        ]

    def format(self, citation: DraftCitation, formatter: CitationFormatterPort) -> str:
        return formatter.format(citation)
