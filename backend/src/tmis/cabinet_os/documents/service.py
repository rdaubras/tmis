import uuid
from datetime import UTC, datetime

from tmis.cabinet_os.documents.ports import CabinetDocumentStorePort
from tmis.cabinet_os.documents.schemas import CabinetDocument, DocumentCategory


class CabinetDocumentService:
    """Implements `CabinetDocumentServicePort` (see
    docs/39-cabinet-os.md — Documents)."""

    def __init__(self, store: CabinetDocumentStorePort) -> None:
        self._store = store

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
    ) -> CabinetDocument:
        document = CabinetDocument(
            id=str(uuid.uuid4()),
            firm_id=firm_id,
            client_id=client_id,
            filename=filename,
            storage_ref=storage_ref,
            category=category,
            case_id=case_id,
            die_record_id=die_record_id,
            uploaded_by=uploaded_by,
            size_bytes=size_bytes,
            uploaded_at=datetime.now(UTC),
        )
        self._store.save(document)
        return document

    def recategorize(self, document_id: str, category: DocumentCategory) -> CabinetDocument:
        document = self._store.get(document_id)
        if document is None:
            raise ValueError(f"Unknown document {document_id!r}")
        document.category = category
        self._store.save(document)
        return document

    def list_for_client(self, client_id: str) -> list[CabinetDocument]:
        return self._store.list_for_client(client_id)

    def list_for_case(self, case_id: str) -> list[CabinetDocument]:
        return self._store.list_for_case(case_id)
