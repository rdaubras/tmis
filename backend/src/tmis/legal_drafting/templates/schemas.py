from dataclasses import dataclass, field
from enum import Enum


class DocumentType(str, Enum):
    """The nine document types the Sprint 7 prompt asks for."""

    CONSULTATION = "consultation"
    NOTE_INTERNE = "note_interne"
    COURRIER = "courrier"
    MISE_EN_DEMEURE = "mise_en_demeure"
    REQUETE = "requete"
    ASSIGNATION = "assignation"
    CONCLUSIONS = "conclusions"
    MEMOIRE = "memoire"
    SYNTHESE = "synthese"


class SectionRole(str, Enum):
    """Generic structural roles shared across templates, so the
    Paragraph Engine can generate content for a section without knowing
    which of the nine document types it belongs to (see
    docs/28-legal-drafting.md — Template Engine)."""

    HEADER = "header"
    CONTEXT = "context"
    FACTS = "facts"
    LEGAL_DISCUSSION = "legal_discussion"
    ARGUMENTS = "arguments"
    RECOMMENDATIONS = "recommendations"
    CONCLUSION = "conclusion"
    SIGNATURE = "signature"


@dataclass(frozen=True, slots=True)
class TemplateSection:
    """One section a template requires, in the order it must appear.
    `depends_on` lists the `key`s of sections that must be generated
    first — e.g. a legal discussion depends on the facts already being
    laid out — checked by `sections.DocumentBuilder` (see
    docs/28-legal-drafting.md — Document Builder)."""

    key: str
    role: SectionRole
    title: str
    order: int
    required: bool = True
    depends_on: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class DocumentTemplate:
    """A versioned document template: structure, sections, variables,
    rules and controls (see docs/28-legal-drafting.md — Template
    Engine). Templates are immutable — a new version is a new object,
    never a mutation of an existing one, so a draft always keeps a
    stable reference to the exact template version it was built from.
    """

    id: str
    document_type: DocumentType
    version: int
    name: str
    sections: tuple[TemplateSection, ...]
    variables: tuple[str, ...] = field(default_factory=tuple)
    rules: tuple[str, ...] = field(default_factory=tuple)
    controls: tuple[str, ...] = field(default_factory=tuple)
