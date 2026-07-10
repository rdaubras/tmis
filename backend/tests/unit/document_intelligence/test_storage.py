from tmis.document_intelligence.schemas.document import ProcessingStatus
from tmis.document_intelligence.schemas.record import DocumentRecord
from tmis.document_intelligence.storage.in_memory_store import InMemoryDocumentStore


def test_save_then_get_roundtrips() -> None:
    store = InMemoryDocumentStore()
    record = DocumentRecord(
        document_id="doc-1",
        filename="bail.txt",
        status=ProcessingStatus.PROCESSED,
        raw_bytes=b"x",
    )
    store.save(record)
    assert store.get("doc-1") == record


def test_get_missing_document_returns_none() -> None:
    assert InMemoryDocumentStore().get("missing") is None


def test_list_ids_returns_every_saved_document() -> None:
    store = InMemoryDocumentStore()
    store.save(
        DocumentRecord(
            document_id="doc-1", filename="a.txt", status=ProcessingStatus.RECEIVED, raw_bytes=b""
        )
    )
    store.save(
        DocumentRecord(
            document_id="doc-2", filename="b.txt", status=ProcessingStatus.RECEIVED, raw_bytes=b""
        )
    )
    assert set(store.list_ids()) == {"doc-1", "doc-2"}


def test_save_overwrites_existing_record_with_same_id() -> None:
    store = InMemoryDocumentStore()
    store.save(
        DocumentRecord(
            document_id="doc-1", filename="a.txt", status=ProcessingStatus.RECEIVED, raw_bytes=b""
        )
    )
    store.save(
        DocumentRecord(
            document_id="doc-1",
            filename="a.txt",
            status=ProcessingStatus.PROCESSED,
            raw_bytes=b"",
        )
    )
    record = store.get("doc-1")
    assert record is not None
    assert record.status == ProcessingStatus.PROCESSED
