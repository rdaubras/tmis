"""The sprint's "Modèle de consultation" example plugin — demonstrates
`tmis.platform_sdk.document_sdk`: variables, ordered sections, and a
reference to a Sprint 7 `DocumentType`."""

from typing import Any

from tmis.legal_drafting.templates.schemas import DocumentType
from tmis.platform_sdk.document_sdk.base import BaseDocumentTemplatePlugin
from tmis.platform_sdk.document_sdk.schemas import (
    DocumentTemplateDefinition,
    TemplateSectionRef,
    TemplateVariable,
)

PLUGIN_ID = "document-template-consultation"

_DEFINITION = DocumentTemplateDefinition(
    id=PLUGIN_ID,
    name="Modèle de consultation",
    document_type=DocumentType.CONSULTATION,
    variables=(
        TemplateVariable("client_name", "Nom du client"),
        TemplateVariable("question", "Question juridique posée"),
        TemplateVariable("recommandation", "Recommandation du cabinet", required=False),
    ),
    sections=(
        TemplateSectionRef("header", "En-tête", order=1),
        TemplateSectionRef("question", "Question posée", order=2),
        TemplateSectionRef("analysis", "Analyse", order=3),
    ),
    validations=("client_name et question sont obligatoires",),
)


class DocumentTemplateConsultationPlugin(BaseDocumentTemplatePlugin):
    def __init__(self) -> None:
        super().__init__(plugin_id=PLUGIN_ID, definition=_DEFINITION)

    def render_section(self, section_key: str, variables: dict[str, Any]) -> str:
        if section_key == "header":
            return f"Consultation juridique — {variables['client_name']}"
        if section_key == "question":
            return f"Question posée : {variables['question']}"
        if section_key == "analysis":
            return str(variables.get("recommandation", "Analyse à compléter."))
        return ""
