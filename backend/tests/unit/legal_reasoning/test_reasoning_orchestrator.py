import pytest

from tmis.ai.schemas.provider import ModelResponse
from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.case_intelligence.facts.schemas import Fact
from tmis.legal_reasoning.reasoner.orchestrator import ReasoningOrchestrator
from tmis.legal_research.search.schemas import ResearchResponse, ResearchResult


class _FakeCasePort:
    def __init__(self, profile: CaseProfile | None) -> None:
        self._profile = profile

    def get_profile(self, case_id: str) -> CaseProfile | None:
        return self._profile


class _FakeResearchPort:
    def __init__(self, results: list[ResearchResult]) -> None:
        self._results = results

    async def search(
        self, query: str, *, case_id: str | None = None
    ) -> ResearchResponse:
        return ResearchResponse(
            search_id="search-1",
            query=query,
            results=tuple(self._results),
            connectors_used=tuple({r.connector for r in self._results}),
            duration_ms=1.0,
        )


class _FakeKernel:
    async def complete(self, prompt: str) -> ModelResponse:
        return ModelResponse(text=f"[synthesis] {prompt[:20]}", provider="fake", model="fake")


def _result() -> ResearchResult:
    return ResearchResult(
        id="r1",
        title="Licenciement",
        excerpt="Le licenciement doit être justifié par une cause réelle et sérieuse.",
        connector="codes",
        document_type="code",
        reference="civ-1240",
        date="2020-01-01",
        final_score=0.8,
    )


def _orchestrator(
    profile: CaseProfile | None = None, results: list[ResearchResult] | None = None
) -> ReasoningOrchestrator:
    return ReasoningOrchestrator(
        case_port=_FakeCasePort(profile),
        research_port=_FakeResearchPort(results or [_result()]),
        kernel=_FakeKernel(),
    )


@pytest.mark.asyncio
async def test_reason_returns_a_session_with_hypotheses() -> None:
    session = await _orchestrator().reason("Le licenciement est-il fondé ?")
    assert len(session.hypotheses) == 2
    assert session.question == "Le licenciement est-il fondé ?"


@pytest.mark.asyncio
async def test_reason_builds_arguments_from_research_results() -> None:
    session = await _orchestrator().reason("Le licenciement est-il fondé ?")
    assert session.arguments


@pytest.mark.asyncio
async def test_reason_computes_a_confidence_score_per_hypothesis() -> None:
    session = await _orchestrator().reason("Le licenciement est-il fondé ?")
    assert set(session.confidence_scores) == {h.id for h in session.hypotheses}


@pytest.mark.asyncio
async def test_reason_detects_conflicts_from_case_facts() -> None:
    fact = Fact(
        id="f1",
        description="Le licenciement a eu lieu le 3 mars.",
        confidence=0.8,
        source_document_ids={"d1"},
        contradicting_document_ids={"d2"},
    )
    profile = CaseProfile(case_id="case-1", title="Test", facts=[fact])

    session = await _orchestrator(profile=profile).reason(
        "Le licenciement est-il fondé ?", case_id="case-1"
    )

    assert session.conflicts


@pytest.mark.asyncio
async def test_reason_produces_a_synthesis_via_the_kernel() -> None:
    session = await _orchestrator().reason("Le licenciement est-il fondé ?")
    assert session.synthesis.startswith("[synthesis]")


@pytest.mark.asyncio
async def test_reason_builds_an_explanation_and_decision_graph() -> None:
    session = await _orchestrator().reason("Le licenciement est-il fondé ?")
    assert session.explanation is not None
    assert session.decision_graph is not None
    assert session.decision_graph.nodes


@pytest.mark.asyncio
async def test_reason_proposes_strategies_for_every_hypothesis() -> None:
    session = await _orchestrator().reason("Le licenciement est-il fondé ?")
    assert {s.hypothesis_id for s in session.strategies} == {h.id for h in session.hypotheses}


@pytest.mark.asyncio
async def test_get_session_retrieves_a_past_session() -> None:
    orchestrator = _orchestrator()
    session = await orchestrator.reason("Le licenciement est-il fondé ?")
    assert orchestrator.get_session(session.id) is session


@pytest.mark.asyncio
async def test_get_session_returns_none_for_unknown_id() -> None:
    assert _orchestrator().get_session("unknown") is None


@pytest.mark.asyncio
async def test_reason_publishes_all_sprint6_events() -> None:
    published_types: list[str] = []

    orchestrator = _orchestrator()

    async def _record(event: object) -> None:
        published_types.append(type(event).__name__)

    from tmis.ai.events.events import (
        ArgumentAdded,
        ConfidenceCalculated,
        CounterArgumentAdded,
        HypothesisCreated,
        ReasoningCompleted,
        ReasoningStarted,
    )

    for event_type in (
        ReasoningStarted,
        HypothesisCreated,
        ArgumentAdded,
        CounterArgumentAdded,
        ConfidenceCalculated,
        ReasoningCompleted,
    ):
        orchestrator.event_bus.subscribe(event_type, _record)

    await orchestrator.reason("Le licenciement est-il fondé ?")

    assert "ReasoningStarted" in published_types
    assert "HypothesisCreated" in published_types
    assert "ArgumentAdded" in published_types
    assert "ConfidenceCalculated" in published_types
    assert "ReasoningCompleted" in published_types


@pytest.mark.asyncio
async def test_reason_works_without_a_case_id() -> None:
    session = await _orchestrator().reason("Question sans dossier ?")
    assert session.case_id is None
    assert session.hypotheses
