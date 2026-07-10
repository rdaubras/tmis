from typing import Protocol

from tmis.cabinet_os.documents.schemas import CabinetDocument, DocumentCategory


class CabinetDocumentStorePort(Protocol):
    def get(self, document_id: str) -> CabinetDocument | None: ...

    def save(self, document: CabinetDocument) -> None: ...

    def list_for_client(self, client_id: str) -> list[CabinetDocument]: ...

    def list_for_case(self, case_id: str) -> list[CabinetDocument]: ...


class CabinetDocumentServicePort(Protocol):
    """Port implemented by every interchangeable cabinet document
    service."""

    def register(
        self,
        firm_id: str,
        client_id: str,
        filename: str,
        storage_ref: str,
        *,
        category: DocumentCategory = DocumentCategory.OTHER,
        case_id: str | None = None,
        die_record_id: str | None = None,
        uploaded_by: str = "",
        size_bytes: int = 0,
    ) -> CabinetDocument: ...

    def recategorize(self, document_id: str, category: DocumentCategory) -> CabinetDocument: ...

    def list_for_client(self, client_id: str) -> list[CabinetDocument]: ...

    def list_for_case(self, case_id: str) -> list[CabinetDocument]: ...
