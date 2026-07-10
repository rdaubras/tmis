from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DraftCitation:
    """A citation anchored to a precise location in the draft — the
    document, the section, and the paragraph — plus the documentary
    source it points to (see docs/28-legal-drafting.md — Citation
    Engine). Extends `tmis.legal_research.citations.schemas.ResearchCitation`
    conceptually, but a `DraftCitation` is anchored in the *document*
    structure rather than in a search result, so it is its own schema.
    """

    id: str
    document_id: str
    section_id: str
    paragraph_id: str
    source_type: str
    source_id: str
    reference: str
    excerpt: str
