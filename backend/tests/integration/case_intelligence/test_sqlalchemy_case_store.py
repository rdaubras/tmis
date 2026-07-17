"""Integration test for `SQLAlchemyCaseStore` against a real (sqlite)
database — exercises the actual SQL round-trip, not a mock."""

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from tmis.case_intelligence.actors.schemas import Actor, ActorType, CaseActorRole
from tmis.case_intelligence.cases.adapters.sqlalchemy_store import SQLAlchemyCaseStore
from tmis.case_intelligence.cases.ports import CaseStorePort
from tmis.case_intelligence.cases.schemas import CaseProfile, CaseTask
from tmis.case_intelligence.evidence.schemas import EvidenceConfidence, EvidenceLink
from tmis.case_intelligence.facts.schemas import Fact
from tmis.case_intelligence.issues.schemas import IssueStatus, LegalIssue
from tmis.case_intelligence.timeline.schemas import CaseTimelineEntry, TimelineInconsistency
from tmis.core.db.base import Base

_FIRM_ID = uuid.uuid4()
_OTHER_FIRM_ID = uuid.uuid4()


@pytest.fixture
def session_factory() -> Iterator[sessionmaker[Session]]:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine, tables=[Base.metadata.tables["case_profiles"]])
    yield sessionmaker(bind=engine)
    Base.metadata.drop_all(engine, tables=[Base.metadata.tables["case_profiles"]])


@pytest.fixture
def store(session_factory: sessionmaker[Session]) -> SQLAlchemyCaseStore:
    return SQLAlchemyCaseStore(session_factory=session_factory, firm_id=_FIRM_ID)


def _sample_profile(case_id: str, *, title: str = "Dupont c. Martin") -> CaseProfile:
    client = Actor(
        id="actor-1",
        type=ActorType.PERSON,
        name="Jean Dupont",
        aliases={"J. Dupont"},
        source_document_ids={"doc-1"},
    )
    opposing = Actor(
        id="actor-2",
        type=ActorType.COMPANY,
        name="Martin SARL",
        aliases=set(),
        source_document_ids={"doc-2"},
    )
    entry = CaseTimelineEntry(
        date="2026-01-01",
        description="Signature du contrat",
        document_ids=("doc-1",),
        confidence=0.9,
    )
    return CaseProfile(
        case_id=case_id,
        title=title,
        actors=[client, opposing],
        actor_roles={"actor-1": CaseActorRole.CLIENT, "actor-2": CaseActorRole.OPPOSING_PARTY},
        document_ids={"doc-1", "doc-2"},
        timeline=[entry],
        timeline_inconsistencies=[
            TimelineInconsistency(date="2026-01-01", entries=(entry,), reason="conflit de dates")
        ],
        facts=[
            Fact(
                id="fact-1",
                description="Le contrat a été signé le 2026-01-01",
                confidence=0.85,
                dates=("2026-01-01",),
                source_document_ids={"doc-1"},
                confirming_document_ids={"doc-2"},
                contradicting_document_ids=set(),
            )
        ],
        evidence_links=[
            EvidenceLink(
                fact_id="fact-1", document_id="doc-1", confidence=EvidenceConfidence.DIRECT
            )
        ],
        legal_issues=[
            LegalIssue(
                id="issue-1",
                description="Validité du contrat",
                related_fact_ids=("fact-1",),
                confidence=0.7,
                status=IssueStatus.OPEN,
            )
        ],
        tasks=[CaseTask(id="task-1", description="Vérifier la signature", done=False)],
        ai_history=["2026-01-01T00:00:00+00:00: created"],
        is_deleted=False,
        created_at=datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC),
        updated_at=datetime(2026, 1, 2, 12, 0, 0, tzinfo=UTC),
    )


def test_store_implements_case_store_port(store: SQLAlchemyCaseStore) -> None:
    port: CaseStorePort = store
    assert port is not None


def test_save_then_get_round_trips_every_field(store: SQLAlchemyCaseStore) -> None:
    profile = _sample_profile("case-1")

    store.save(profile)
    fetched = store.get("case-1")

    assert fetched is not None
    assert fetched == profile


def test_get_missing_case_returns_none(store: SQLAlchemyCaseStore) -> None:
    assert store.get("does-not-exist") is None


def test_list_ids_returns_distinct_case_ids(store: SQLAlchemyCaseStore) -> None:
    store.save(_sample_profile("case-1"))
    store.save(_sample_profile("case-2"))

    assert sorted(store.list_ids()) == ["case-1", "case-2"]


def test_get_or_create_returns_existing_profile_if_present(store: SQLAlchemyCaseStore) -> None:
    profile = _sample_profile("case-1")
    store.save(profile)

    result = store.get_or_create("case-1", "Some other title")

    assert result == profile


def test_get_or_create_creates_and_persists_new_profile_if_absent(
    store: SQLAlchemyCaseStore,
) -> None:
    result = store.get_or_create("case-new", "Brand New Case")

    assert result.case_id == "case-new"
    assert result.title == "Brand New Case"
    assert store.get("case-new") == result


def test_resaving_existing_case_id_overwrites_rather_than_duplicates(
    store: SQLAlchemyCaseStore,
) -> None:
    store.save(_sample_profile("case-1", title="Original Title"))
    store.save(_sample_profile("case-1", title="Updated Title"))

    fetched = store.get("case-1")
    assert fetched is not None
    assert fetched.title == "Updated Title"
    assert store.list_ids() == ["case-1"]


def test_a_profile_saved_by_one_firm_is_invisible_to_another(
    session_factory: sessionmaker[Session],
) -> None:
    store_a = SQLAlchemyCaseStore(session_factory=session_factory, firm_id=_FIRM_ID)
    store_b = SQLAlchemyCaseStore(session_factory=session_factory, firm_id=_OTHER_FIRM_ID)

    store_a.save(_sample_profile("case-1"))

    assert store_b.get("case-1") is None
    assert store_b.list_ids() == []
    assert store_a.get("case-1") is not None
