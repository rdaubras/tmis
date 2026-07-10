from dataclasses import dataclass, field

from tmis.legal_drafting.paragraphs.schemas import Paragraph


@dataclass(slots=True)
class Section:
    """One assembled section of a draft — the `TemplateSection.key` it
    was built from, its title/order (copied from the template at build
    time), and the paragraphs generated for it (see
    docs/28-legal-drafting.md — Document Builder)."""

    id: str
    key: str
    title: str
    order: int
    paragraphs: list[Paragraph] = field(default_factory=list)
    depends_on: tuple[str, ...] = field(default_factory=tuple)
