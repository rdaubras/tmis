from tmis.cabinet_os.documents.schemas import CabinetDocument


class InMemoryCabinetDocumentStore:
    """Implements `CabinetDocumentStorePort` with an in-memory dict."""

    def __init__(self) -> None:
        self._documents: dict[str, CabinetDocument] = {}

    def get(self, document_id: str) -> CabinetDocument | None:
        return self._documents.get(document_id)

    def save(self, document: CabinetDocument) -> None:
        self._documents[document.id] = document

    def list_for_client(self, client_id: str) -> list[CabinetDocument]:
        return [d for d in self._documents.values() if d.client_id == client_id]

    def list_for_case(self, case_id: str) -> list[CabinetDocument]:
        return [d for d in self._documents.values() if d.case_id == case_id]
