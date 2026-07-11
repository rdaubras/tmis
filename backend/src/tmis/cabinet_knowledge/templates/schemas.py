from dataclasses import dataclass
from typing import Any

from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeObject, KnowledgeType
from tmis.legal_drafting.templates.schemas import DocumentType


@dataclass(frozen=True, slots=True)
class CabinetTemplate:
    """A cabinet-specific customization layered on top of a Sprint 7
    `DocumentType` (headers/sections/rules) — this is the firm's own
    preferred structure/wording for that document type, not a
    replacement for `tmis.legal_drafting.templates.DocumentTemplate`."""

    id: str
    document_type: DocumentType
    title: str
    structure: tuple[str, ...]
    body_variables: tuple[str, ...] = ()


def template_to_content(template: CabinetTemplate) -> dict[str, Any]:
    return {
        "document_type": template.document_type.value,
        "structure": list(template.structure),
        "body_variables": list(template.body_variables),
    }


def template_from_knowledge_object(obj: KnowledgeObject) -> CabinetTemplate:
    if obj.type is not KnowledgeType.TEMPLATE:
        raise ValueError(f"{obj.id} is not a template (type={obj.type.value})")
    return CabinetTemplate(
        id=obj.id,
        document_type=DocumentType(obj.content["document_type"]),
        title=obj.title,
        structure=tuple(obj.content["structure"]),
        body_variables=tuple(obj.content.get("body_variables", ())),
    )
