"""Integration test for `SQLAlchemyDocumentStore` against a real (sqlite)
database — exercises the actual SQL round-trip, not a mock."""

import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from tmis.core.db.base import Base
from tmis.document_intelligence.adapters.sqlalchemy_store import SQLAlchemyDocumentStore
from tmis.document_intelligence.schemas.classification import ClassificationResult, DocumentCategory
from tmis.document_intelligence.schemas.document import ProcessingStatus
from tmis.document_intelligence.schemas.entities import EntityType, ExtractedEntity
from tmis.document_intelligence.schemas.layout import BlockType, LayoutBlock
from tmis.document_intelligence.schemas.metadata import DocumentMetadata
from tmis.document_intelligence.schemas.record import DocumentRecord
from tmis.document_intelligence.schemas.timeline import TimelineEvent
from tmis.document_intelligence.storage.ports import DocumentStorePort


@pytest.fixture
def session_factory() -> Iterator[sessionmaker[Session]]:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine, tables=[Base.metadata.tables["document_records"]])
    yield sessionmaker(bind=engine)
    Base.metadata.drop_all(engine, tables=[Base.metadata.tables["document_records"]])


_FIRM_ID = uuid.uuid4()


@pytest.fixture
def store(session_factory: sessionmaker[Session]) -> SQLAlchemyDocumentStore:
    return SQLAlchemyDocumentStore(session_factory=session_factory, firm_id=_FIRM_ID)


def _sample_record(document_id: str, *, filename: str = "contrat.pdf") -> DocumentRecord:
    return DocumentRecord(
        document_id=document_id,
        filename=filename,
        status=ProcessingStatus.PROCESSED,
        raw_bytes=b"%PDF-1.4 sample bytes",
        ocr_text="Contrat de bail...",
        layout_blocks=[LayoutBlock(order=0, type=BlockType.TITLE, content="Contrat de bail")],
        classification=ClassificationResult(category=DocumentCategory.CONTRACT, confidence=0.9),
        metadata=DocumentMetadata(
            author=None,
            created_at=None,
            language="fr",
            content_type="application/pdf",
            size_bytes=21,
            page_count=1,
            source="upload",
            version=1,
            sha256="abc123",
            ocr_confidence=0.95,
        ),
        entities=[
            ExtractedEntity(type=EntityType.PERSON, value="Jean Dupont", confidence=0.8),
        ],
        timeline_events=[
            TimelineEvent(
                date="2026-01-01", description="Signature", document_id=document_id, confidence=0.7
            )
        ],
        chunk_ids=["chunk-1", "chunk-2"],
        warnings=["ocr_low_confidence"],
    )


def test_store_implements_document_store_port(store: SQLAlchemyDocumentStore) -> None:
    port: DocumentStorePort = store
    assert port is not None


def test_save_then_get_round_trips_every_field(store: SQLAlchemyDocumentStore) -> None:
    record = _sample_record("doc-1")

    store.save(record)
    fetched = store.get("doc-1")

    assert fetched is not None
    assert fetched.document_id == record.document_id
    assert fetched.filename == record.filename
    assert fetched.status == record.status
    assert fetched.raw_bytes == record.raw_bytes
    assert fetched.ocr_text == record.ocr_text
    assert fetched.layout_blocks == record.layout_blocks
    assert fetched.classification == record.classification
    assert fetched.metadata == record.metadata
    assert fetched.entities == record.entities
    assert fetched.timeline_events == record.timeline_events
    assert fetched.chunk_ids == record.chunk_ids
    assert fetched.warnings == record.warnings


def test_get_missing_document_returns_none(store: SQLAlchemyDocumentStore) -> None:
    assert store.get("does-not-exist") is None


def test_list_ids_returns_distinct_document_ids(store: SQLAlchemyDocumentStore) -> None:
    store.save(_sample_record("doc-1"))
    store.save(_sample_record("doc-2"))

    assert sorted(store.list_ids()) == ["doc-1", "doc-2"]


def test_save_never_overwrites_in_place_new_version_is_a_new_row(
    store: SQLAlchemyDocumentStore,
) -> None:
    store.save(_sample_record("doc-1", filename="v1.pdf"))
    store.save(_sample_record("doc-1", filename="v2.pdf"))

    assert store.get("doc-1") is not None
    assert store.get("doc-1").filename == "v2.pdf"  # type: ignore[union-attr]
    assert store.list_ids() == ["doc-1"]

    versions = store.list_versions("doc-1")
    assert [v.filename for v in versions] == ["v1.pdf", "v2.pdf"]


def test_a_document_saved_by_one_firm_is_invisible_to_another(
    session_factory: sessionmaker[Session],
) -> None:
    """The central guarantee of ADR-DOCINT-01 (docs/14-document-
    intelligence.md): `raw_bytes` — the uploaded file itself — must never
    resolve for a `firm_id` that did not write it."""
    store_a = SQLAlchemyDocumentStore(session_factory=session_factory, firm_id=uuid.uuid4())
    store_b = SQLAlchemyDocumentStore(session_factory=session_factory, firm_id=uuid.uuid4())
    store_a.save(_sample_record("doc-1"))

    assert store_b.get("doc-1") is None
    assert store_b.list_ids() == []
    assert store_b.list_versions("doc-1") == []
    fetched = store_a.get("doc-1")
    assert fetched is not None
    assert fetched.raw_bytes == b"%PDF-1.4 sample bytes"
