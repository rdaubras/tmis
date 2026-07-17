"""Integration test for `SQLAlchemyDraftDocumentStore` against a real
(sqlite) database — exercises the actual SQL round-trip, not a mock."""

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from tmis.core.db.base import Base
from tmis.legal_drafting.citations.schemas import DraftCitation
from tmis.legal_drafting.documents.ports import DocumentStorePort
from tmis.legal_drafting.documents.schemas import Document, DraftWorkflowStatus
from tmis.legal_drafting.documents.sqlalchemy_store import SQLAlchemyDraftDocumentStore
from tmis.legal_drafting.paragraphs.schemas import Paragraph
from tmis.legal_drafting.review.schemas import ReviewFinding, ReviewFindingType
from tmis.legal_drafting.sections.schemas import Section
from tmis.legal_drafting.templates.schemas import DocumentType

_FIRM_ID = uuid.uuid4()
_OTHER_FIRM_ID = uuid.uuid4()


@pytest.fixture
def session_factory() -> Iterator[sessionmaker[Session]]:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine, tables=[Base.metadata.tables["drafting_documents"]])
    yield sessionmaker(bind=engine)
    Base.metadata.drop_all(engine, tables=[Base.metadata.tables["drafting_documents"]])


@pytest.fixture
def session(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    with session_factory() as session:
        yield session


@pytest.fixture
def store(session: Session) -> SQLAlchemyDraftDocumentStore:
    return SQLAlchemyDraftDocumentStore(session, _FIRM_ID)


def _sample_document(document_id: str, *, title: str = "Mise en demeure") -> Document:
    paragraph = Paragraph(
        id="para-1",
        section_key="facts",
        order=1,
        text="Les faits sont les suivants...",
        origin="paragraph_engine",
        fact_ids=("fact-1", "fact-2"),
        reference_ids=("ref-1",),
        evidence_ids=("ev-1",),
        hypothesis_ids=("hyp-1",),
    )
    section = Section(
        id="sec-1",
        key="facts",
        title="Faits",
        order=1,
        paragraphs=[paragraph],
        depends_on=("header",),
    )
    citation = DraftCitation(
        id="cit-1",
        document_id=document_id,
        section_id="sec-1",
        paragraph_id="para-1",
        source_type="legifrance",
        source_id="art-1224",
        reference="Art. 1224 C. civ.",
        excerpt="En cas d'inexécution...",
    )
    finding = ReviewFinding(
        id="find-1",
        type=ReviewFindingType.MISSING_REFERENCE,
        description="Le paragraphe 2 manque de référence.",
        section_id="sec-1",
        paragraph_id="para-1",
    )
    return Document(
        id=document_id,
        template_id="tmpl-mise-en-demeure-v1",
        document_type=DocumentType.MISE_EN_DEMEURE,
        case_id="case-1",
        title=title,
        sections=[section],
        citations=[citation],
        review_findings=[finding],
        status=DraftWorkflowStatus.UNDER_REVIEW,
        source_question="Le bail peut-il être résilié ?",
        reasoning_session_id="sess-1",
        style_profile_id="cabinet-default",
        variables={"client_name": "Société Alpha", "date": "2026-07-14"},
        created_at=datetime(2026, 7, 14, 9, 0, tzinfo=UTC),
        updated_at=datetime(2026, 7, 14, 10, 30, tzinfo=UTC),
    )


def test_store_implements_document_store_port(store: SQLAlchemyDraftDocumentStore) -> None:
    port: DocumentStorePort = store
    assert port is not None


def test_save_then_get_round_trips_every_field(store: SQLAlchemyDraftDocumentStore) -> None:
    document = _sample_document("doc-1")

    store.save(document)
    fetched = store.get("doc-1")

    assert fetched is not None
    assert fetched.id == document.id
    assert fetched.template_id == document.template_id
    assert fetched.document_type == document.document_type
    assert fetched.case_id == document.case_id
    assert fetched.title == document.title
    assert fetched.sections == document.sections
    assert fetched.citations == document.citations
    assert fetched.review_findings == document.review_findings
    assert fetched.status == document.status
    assert fetched.source_question == document.source_question
    assert fetched.reasoning_session_id == document.reasoning_session_id
    assert fetched.style_profile_id == document.style_profile_id
    assert fetched.variables == document.variables
    assert fetched.created_at == document.created_at
    assert fetched.updated_at == document.updated_at
    assert fetched == document
    assert fetched.is_draft is True


def test_get_missing_document_returns_none(store: SQLAlchemyDraftDocumentStore) -> None:
    assert store.get("does-not-exist") is None


def test_list_ids_returns_distinct_document_ids(store: SQLAlchemyDraftDocumentStore) -> None:
    store.save(_sample_document("doc-1"))
    store.save(_sample_document("doc-2"))

    assert sorted(store.list_ids()) == ["doc-1", "doc-2"]


def test_save_upserts_existing_id_in_place(store: SQLAlchemyDraftDocumentStore) -> None:
    store.save(_sample_document("doc-1", title="v1"))
    store.save(_sample_document("doc-1", title="v2"))

    fetched = store.get("doc-1")
    assert fetched is not None
    assert fetched.title == "v2"
    assert store.list_ids() == ["doc-1"]


def test_a_document_saved_by_one_firm_is_invisible_to_another(session: Session) -> None:
    store_a = SQLAlchemyDraftDocumentStore(session, _FIRM_ID)
    store_b = SQLAlchemyDraftDocumentStore(session, _OTHER_FIRM_ID)

    store_a.save(_sample_document("doc-1"))

    assert store_b.get("doc-1") is None
    assert store_b.list_ids() == []
    assert store_a.list_ids() == ["doc-1"]
