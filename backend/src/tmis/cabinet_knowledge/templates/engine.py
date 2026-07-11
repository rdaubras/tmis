from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeType
from tmis.cabinet_knowledge.templates.schemas import (
    CabinetTemplate,
    template_from_knowledge_object,
    template_to_content,
)
from tmis.legal_drafting.templates.schemas import DocumentType


class CabinetTemplateEngine:
    def __init__(self, knowledge_space: KnowledgeSpace) -> None:
        self._knowledge_space = knowledge_space

    def create_template(
        self,
        firm_id: str,
        title: str,
        document_type: DocumentType,
        structure: tuple[str, ...],
        author: str,
        body_variables: tuple[str, ...] = (),
    ) -> CabinetTemplate:
        template_shell = CabinetTemplate(
            id="",
            document_type=document_type,
            title=title,
            structure=structure,
            body_variables=body_variables,
        )
        obj = self._knowledge_space.create(
            firm_id,
            KnowledgeType.TEMPLATE,
            title,
            template_to_content(template_shell),
            author,
            tags=frozenset({document_type.value}),
        )
        return template_from_knowledge_object(obj)

    def get_template(self, firm_id: str, template_id: str) -> CabinetTemplate:
        obj = self._knowledge_space.get(firm_id, template_id)
        if obj is None:
            raise KeyError(template_id)
        return template_from_knowledge_object(obj)

    def list_templates(
        self, firm_id: str, document_type: DocumentType | None = None
    ) -> list[CabinetTemplate]:
        objects = self._knowledge_space.list(firm_id, type_=KnowledgeType.TEMPLATE)
        templates = [template_from_knowledge_object(obj) for obj in objects]
        if document_type is not None:
            templates = [t for t in templates if t.document_type is document_type]
        return templates
