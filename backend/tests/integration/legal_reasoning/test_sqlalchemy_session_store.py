"""Integration test for `SQLAlchemySessionStore` against a real (sqlite)
database — exercises the actual SQL round-trip, not a mock."""

from collections.abc import Iterator
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from tmis.core.db.base import Base
from tmis.legal_reasoning.arguments.schemas import Argument
from tmis.legal_reasoning.confidence.schemas import ConfidenceScore
from tmis.legal_reasoning.conflicts.schemas import Conflict, ConflictType
from tmis.legal_reasoning.counter_arguments.schemas import CounterArgument
from tmis.legal_reasoning.decision_graph.schemas import (
    DecisionEdge,
    DecisionGraph,
    DecisionNode,
    DecisionNodeType,
)
from tmis.legal_reasoning.evidence.schemas import ReasoningEvidenceLink
from tmis.legal_reasoning.explanations.schemas import Explanation
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis, HypothesisStatus
from tmis.legal_reasoning.reasoner.ports import SessionStorePort
from tmis.legal_reasoning.reasoner.schemas import ReasoningSession
from tmis.legal_reasoning.reasoner.sqlalchemy_store import SQLAlchemySessionStore
from tmis.legal_reasoning.strategy.schemas import StrategyOption


@pytest.fixture
def session_factory() -> Iterator[sessionmaker[Session]]:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine, tables=[Base.metadata.tables["reasoning_sessions"]])
    yield sessionmaker(bind=engine)
    Base.metadata.drop_all(engine, tables=[Base.metadata.tables["reasoning_sessions"]])


@pytest.fixture
def store(session_factory: sessionmaker[Session]) -> SQLAlchemySessionStore:
    return SQLAlchemySessionStore(session_factory=session_factory)


# Naive datetime: SQLite's DateTime column drops tzinfo on round-trip
# (a driver quirk of this test's in-memory fixture, not of Postgres), so
# the fixture uses a naive datetime to keep the round-trip assertion exact
# regardless of backend (matches the convention in
# tests/integration/legal_research/test_sqlalchemy_research_history_store.py).
_BASE_TIME = datetime(2026, 7, 14, 10, 30, 0)


def _sample_session(session_id: str, *, synthesis: str = "Synthèse prudente") -> ReasoningSession:
    hypothesis = Hypothesis(
        id="hyp-1",
        description="Le contrat est résiliable pour manquement.",
        supporting_fact_ids=("fact-1", "fact-2"),
        references=("ref-1",),
        confidence=0.72,
        status=HypothesisStatus.SUPPORTED,
    )
    argument = Argument(
        id="arg-1",
        hypothesis_id="hyp-1",
        claim="La clause 4.2 impose un préavis de 30 jours.",
        source_connector="legifrance",
        source_reference="Art. 1224 C. civ.",
        excerpt="En cas d'inexécution...",
        confidence=0.8,
    )
    counter_argument = CounterArgument(
        id="cnt-1",
        argument_id="arg-1",
        claim="Le préavis a bien été respecté selon la pièce 3.",
        source_connector="dossier",
        source_reference="pièce-3",
        excerpt="Notification envoyée le...",
        confidence=0.4,
    )
    evidence_link = ReasoningEvidenceLink(
        id="ev-1",
        fact_id="fact-1",
        document_id="doc-1",
        hypothesis_id="hyp-1",
        argument_id="arg-1",
        reliability_score=0.9,
    )
    conflict = Conflict(
        id="conf-1",
        type=ConflictType.TEMPORAL_CONTRADICTION,
        description="Deux dates de notification différentes.",
        explanation="Le document A et le document B ne concordent pas.",
        involved_ids=("doc-1", "doc-2"),
    )
    confidence_score = ConfidenceScore(
        hypothesis_id="hyp-1",
        value=0.72,
        explanation="Support argumentaire fort, peu de contre-arguments.",
        factors={"argument_support": 0.8, "evidence_reliability": 0.7},
    )
    strategy = StrategyOption(
        id="strat-1",
        hypothesis_id="hyp-1",
        objective="Obtenir la résiliation judiciaire du contrat.",
        favorable_points=("préavis respecté",),
        risks=("contestation possible",),
        missing_elements=("preuve de la mise en demeure",),
    )
    explanation = Explanation(
        reasoning_steps=("analyse des faits", "génération d'hypothèses"),
        components_used=("case_intelligence", "legal_research"),
        references=("Art. 1224 C. civ.",),
        hypotheses_considered=("hyp-1",),
        limitations=("synthèse non contraignante",),
    )
    decision_graph = DecisionGraph(
        nodes=(
            DecisionNode(id="n1", type=DecisionNodeType.QUESTION, label="Question"),
            DecisionNode(id="n2", type=DecisionNodeType.HYPOTHESIS, label="Hypothèse 1"),
        ),
        edges=(DecisionEdge(source_id="n1", target_id="n2", relation="leads_to"),),
    )
    return ReasoningSession(
        id=session_id,
        question="Le bail peut-il être résilié ?",
        case_id="case-1",
        hypotheses=[hypothesis],
        arguments=[argument],
        counter_arguments=[counter_argument],
        evidence_links=[evidence_link],
        conflicts=[conflict],
        confidence_scores={"hyp-1": confidence_score},
        strategies=[strategy],
        synthesis=synthesis,
        explanation=explanation,
        decision_graph=decision_graph,
        duration_ms=123.45,
        created_at=_BASE_TIME,
    )


def test_store_implements_session_store_port(store: SQLAlchemySessionStore) -> None:
    port: SessionStorePort = store
    assert port is not None


def test_save_then_get_round_trips_every_field(store: SQLAlchemySessionStore) -> None:
    session = _sample_session("sess-1")

    store.save(session)
    fetched = store.get("sess-1")

    assert fetched is not None
    assert fetched.id == session.id
    assert fetched.question == session.question
    assert fetched.case_id == session.case_id
    assert fetched.hypotheses == session.hypotheses
    assert fetched.arguments == session.arguments
    assert fetched.counter_arguments == session.counter_arguments
    assert fetched.evidence_links == session.evidence_links
    assert fetched.conflicts == session.conflicts
    assert fetched.confidence_scores == session.confidence_scores
    assert fetched.strategies == session.strategies
    assert fetched.synthesis == session.synthesis
    assert fetched.explanation == session.explanation
    assert fetched.decision_graph == session.decision_graph
    assert fetched.duration_ms == session.duration_ms
    assert fetched.created_at == session.created_at
    assert fetched == session


def test_get_missing_session_returns_none(store: SQLAlchemySessionStore) -> None:
    assert store.get("does-not-exist") is None


def test_list_ids_returns_distinct_session_ids(store: SQLAlchemySessionStore) -> None:
    store.save(_sample_session("sess-1"))
    store.save(_sample_session("sess-2"))

    assert sorted(store.list_ids()) == ["sess-1", "sess-2"]


def test_save_upserts_existing_id_in_place(store: SQLAlchemySessionStore) -> None:
    store.save(_sample_session("sess-1", synthesis="v1"))
    store.save(_sample_session("sess-1", synthesis="v2"))

    fetched = store.get("sess-1")
    assert fetched is not None
    assert fetched.synthesis == "v2"
    assert store.list_ids() == ["sess-1"]
