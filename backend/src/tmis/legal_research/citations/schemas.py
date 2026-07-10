from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResearchCitation:
    """A traceable citation attached to one research result — every field
    the LRE promises to keep per docs/21-legal-research.md:
    "chaque résultat conserve l'id de la source, le titre, la date, le
    type de document, la référence, l'extrait utilisé"."""

    source_id: str
    title: str
    date: str | None
    document_type: str
    reference: str
    excerpt: str
