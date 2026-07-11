from dataclasses import dataclass

from tmis.legal_drafting.templates.schemas import DocumentType


@dataclass(frozen=True, slots=True)
class TemplateVariable:
    name: str
    description: str
    required: bool = True


@dataclass(frozen=True, slots=True)
class TemplateSectionRef:
    key: str
    title: str
    order: int


@dataclass(frozen=True, slots=True)
class DocumentTemplateDefinition:
    """The sprint's "DOCUMENT TEMPLATE SDK" spec: variables, sections,
    appel aux composants du Drafting Engine, validations.
    `document_type` reuses `tmis.legal_drafting.templates.schemas.
    DocumentType` (Sprint 7) rather than redefining the nine document
    types."""

    id: str
    name: str
    document_type: DocumentType
    variables: tuple[TemplateVariable, ...]
    sections: tuple[TemplateSectionRef, ...]
    validations: tuple[str, ...] = ()
