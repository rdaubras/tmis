from tmis.document_intelligence.schemas.record import DocumentRecord


class InMemoryDocumentStore:
    """Implements `DocumentStorePort` with a process-local dict.

    Default backend for local development and tests; a SQLAlchemy-backed
    implementation is planned for Sprint 6 (see
    docs/09-roadmap-30-sprints.md) — no pipeline change needed to swap it
    in, since the pipeline only depends on `DocumentStorePort`.
    """

    def __init__(self) -> None:
        self._records: dict[str, DocumentRecord] = {}

    def save(self, record: DocumentRecord) -> None:
        self._records[record.document_id] = record

    def get(self, document_id: str) -> DocumentRecord | None:
        return self._records.get(document_id)

    def list_ids(self) -> list[str]:
        return list(self._records)
