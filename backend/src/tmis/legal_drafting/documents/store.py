from tmis.legal_drafting.documents.schemas import Document


class InMemoryDocumentStore:
    """Implements `DocumentStorePort` with an in-memory dict — the
    default deployment for Sprint 7; persistence follows the same
    calendar as the rest of TMIS's engines (Sprint 9)."""

    def __init__(self) -> None:
        self._documents: dict[str, Document] = {}

    def get(self, document_id: str) -> Document | None:
        return self._documents.get(document_id)

    def save(self, document: Document) -> None:
        self._documents[document.id] = document

    def list_ids(self) -> list[str]:
        return list(self._documents)
