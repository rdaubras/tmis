from typing import Protocol

from tmis.legal_drafting.templates.schemas import DocumentTemplate, DocumentType


class TemplateRegistryPort(Protocol):
    """Port implemented by every interchangeable template catalog."""

    def get_latest(self, document_type: DocumentType) -> DocumentTemplate: ...

    def get(self, template_id: str) -> DocumentTemplate | None: ...

    def list_versions(self, document_type: DocumentType) -> list[DocumentTemplate]: ...

    def register(self, template: DocumentTemplate) -> None: ...
