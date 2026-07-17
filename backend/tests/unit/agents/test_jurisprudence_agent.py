import uuid

import pytest

from tmis.agents.contracts import AgentInput, ConfidenceLevel
from tmis.agents.jurisprudence_agent import JurisprudenceAgent
from tmis.ai.cache.in_memory_cache import InMemoryCache
from tmis.ai.schemas.connector import ConnectorDocument
from tmis.ai_fabric.bootstrap import get_ai_intelligence_fabric
from tmis.ai_governance.explainability.engine import ExplainabilityEngine
from tmis.ai_governance.explainability.store import InMemoryExplainabilityStore
from tmis.ai_governance.overview import AIGovernancePlatform
from tmis.case_intelligence.cases.in_memory_store import InMemoryCaseStore
from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.legal_research.cache.research_cache import ResearchCache
from tmis.legal_research.citations.engine import CitationEngine
from tmis.legal_research.evaluation.evaluator import ResearchEvaluator
from tmis.legal_research.history.in_memory_history import InMemoryResearchHistory
from tmis.legal_research.normalization.normalizer import SourceNormalizer
from tmis.legal_research.queries.engine import HeuristicQueryEngine
from tmis.legal_research.queries.schemas import ResearchQuery
from tmis.legal_research.ranking.configurable_ranker import ConfigurableRanker
from tmis.legal_research.search.in_memory_store import InMemoryResearchSearchStore
from tmis.legal_research.search.orchestrator import ResearchOrchestrator
from tmis.legal_research.search.schemas import RelevanceScores
from tmis.legal_research.sources.registry import SourceRegistry

_DECISIONS = [
    ConnectorDocument(
        id="cass-civ1-2021",
        title="Cass. civ. 1re, 12 janvier 2021, n° 19-12.345",
        content="La cour retient la responsabilite contractuelle du vendeur.",
        connector="jurisprudence",
        metadata={"date": "2021-01-12"},
    ),
    ConnectorDocument(
        id="cass-civ1-2019",
        title="Cass. civ. 1re, 3 mai 2019, n° 17-98.765",
        content="La cour ecarte la responsabilite contractuelle en l'absence de faute.",
        connector="jurisprudence",
        metadata={"date": "2019-05-03"},
    ),
]


class _FakeSearch:
    def __init__(self, seen_connector_names: list[list[str] | None] | None = None) -> None:
        self._seen = seen_connector_names

    async def execute(
        self, query: ResearchQuery, *, connector_names: list[str] | None = None
    ) -> tuple[list[ConnectorDocument], list[str], dict[str, RelevanceScores]]:
        if self._seen is not None:
            self._seen.append(connector_names)
        scores = {
            "cass-civ1-2021": RelevanceScores(lexical_score=0.9, vector_score=0.8),
            "cass-civ1-2019": RelevanceScores(lexical_score=0.6, vector_score=0.5),
        }
        return list(_DECISIONS), ["jurisprudence"], scores


class _EmptySearch:
    async def execute(
        self, query: ResearchQuery, *, connector_names: list[str] | None = None
    ) -> tuple[list[ConnectorDocument], list[str], dict[str, RelevanceScores]]:
        return [], [], {}


def _build_orchestrator(search: object | None = None) -> ResearchOrchestrator:
    return ResearchOrchestrator(
        query_engine=HeuristicQueryEngine(),
        search=search or _FakeSearch(),
        normalizer=SourceNormalizer(),
        ranker=ConfigurableRanker(SourceRegistry(), current_year_fn=lambda: 2026),
        citation_engine=CitationEngine(),
        cache=ResearchCache(InMemoryCache(), "firm-1"),
        history=InMemoryResearchHistory(),
        searches=InMemoryResearchSearchStore(),
        evaluator=ResearchEvaluator(),
    )


def _build_governance() -> AIGovernancePlatform:
    from tmis.ai_governance.decision_records.engine import DecisionRecordEngine
    from tmis.ai_governance.decision_records.store import InMemoryDecisionRecordStore
    from tmis.ai_governance.human_validation.engine import HumanValidationEngine
    from tmis.ai_governance.human_validation.store import InMemoryValidationStore
    from tmis.ai_governance.lineage.engine import LineageEngine
    from tmis.ai_governance.lineage.store import InMemoryLineageStore
    from tmis.ai_governance.provenance.engine import ProvenanceEngine
    from tmis.ai_governance.provenance.store import InMemoryProvenanceStore
    from tmis.ai_governance.reasoning_chain.engine import ReasoningChainEngine
    from tmis.ai_governance.reasoning_chain.store import InMemoryReasoningChainStore
    from tmis.ai_governance.traceability.engine import TraceabilityEngine
    from tmis.ai_governance.traceability.store import InMemoryTraceStore

    return AIGovernancePlatform(
        ReasoningChainEngine(InMemoryReasoningChainStore()),
        ProvenanceEngine(InMemoryProvenanceStore()),
        TraceabilityEngine(InMemoryTraceStore()),
        DecisionRecordEngine(InMemoryDecisionRecordStore()),
        HumanValidationEngine(InMemoryValidationStore()),
        LineageEngine(InMemoryLineageStore()),
        ExplainabilityEngine(InMemoryExplainabilityStore()),
    )


@pytest.mark.asyncio
async def test_jurisprudence_agent_without_query_is_low_confidence() -> None:
    agent = JurisprudenceAgent(orchestrator=_build_orchestrator())
    agent_input = AgentInput(task_id=uuid.uuid4(), case_id=None)

    output = await agent.run(agent_input)

    assert output.confidence == ConfidenceLevel.LOW
    assert output.result["results"] == []
    assert output.result["comparison"] is None
    assert any("No query" in warning for warning in output.warnings)


@pytest.mark.asyncio
async def test_jurisprudence_agent_reports_low_confidence_when_the_lre_finds_nothing() -> None:
    agent = JurisprudenceAgent(orchestrator=_build_orchestrator(_EmptySearch()))
    agent_input = AgentInput(
        task_id=uuid.uuid4(), case_id=None, context={"query": "clause introuvable"}
    )

    output = await agent.run(agent_input)

    assert output.confidence == ConfidenceLevel.LOW
    assert output.result["results"] == []
    assert output.result["comparison"] is None
    assert output.citations == []
    assert any("No jurisprudence result found" in warning for warning in output.warnings)


@pytest.mark.asyncio
async def test_jurisprudence_agent_filters_search_on_the_jurisprudence_connector() -> None:
    seen: list[list[str] | None] = []
    agent = JurisprudenceAgent(orchestrator=_build_orchestrator(_FakeSearch(seen)))
    agent_input = AgentInput(
        task_id=uuid.uuid4(), case_id=None, context={"query": "responsabilite contractuelle"}
    )

    await agent.run(agent_input)

    assert seen == [["jurisprudence"]]


@pytest.mark.asyncio
async def test_jurisprudence_agent_runs_a_real_search_and_converts_citations() -> None:
    agent = JurisprudenceAgent(orchestrator=_build_orchestrator())
    agent_input = AgentInput(
        task_id=uuid.uuid4(), case_id=None, context={"query": "responsabilite contractuelle"}
    )

    output = await agent.run(agent_input)

    assert output.confidence == ConfidenceLevel.MEDIUM
    results = output.result["results"]
    assert isinstance(results, list)
    assert len(results) == 2
    assert output.result["query"] == "responsabilite contractuelle"

    assert len(output.citations) == 2
    for citation in output.citations:
        assert citation.connector == "jurisprudence"
        assert citation.excerpt
        assert citation.reference
        assert citation.source_id


@pytest.mark.asyncio
async def test_jurisprudence_agent_generates_a_comparison_without_a_fabric() -> None:
    """Without an injected `AIIntelligenceFabric`, `TMISKernel.complete()`
    still runs through the default provider — mirrors `AnalysisAgent`'s
    own "no fabric" behavior: the generative call is still the single
    call site, just unrouted."""
    agent = JurisprudenceAgent(orchestrator=_build_orchestrator())
    agent_input = AgentInput(
        task_id=uuid.uuid4(), case_id=None, context={"query": "responsabilite contractuelle"}
    )

    output = await agent.run(agent_input)

    assert output.result["comparison"]
    assert output.result["model"] == "default"


@pytest.mark.asyncio
async def test_jurisprudence_agent_routes_comparison_through_the_fabric() -> None:
    agent = JurisprudenceAgent(
        orchestrator=_build_orchestrator(),
        fabric=get_ai_intelligence_fabric(),
        firm_id="firm-test",
    )
    agent_input = AgentInput(
        task_id=uuid.uuid4(), case_id=None, context={"query": "responsabilite contractuelle"}
    )

    output = await agent.run(agent_input)

    assert output.result["comparison"]
    assert output.result["model"] != "default"


@pytest.mark.asyncio
async def test_jurisprudence_agent_uses_case_profile_when_case_id_is_known() -> None:
    case_store = InMemoryCaseStore()
    case_id = str(uuid.uuid4())
    case_store.save(CaseProfile(case_id=case_id, title="Dupont c/ Acme"))

    agent = JurisprudenceAgent(orchestrator=_build_orchestrator(), case_store=case_store)
    agent_input = AgentInput(
        task_id=uuid.uuid4(),
        case_id=case_id,
        context={"query": "responsabilite contractuelle"},
    )

    output = await agent.run(agent_input)

    assert output.result["comparison"]
    assert not any("was not found in the case store" in warning for warning in output.warnings)


@pytest.mark.asyncio
async def test_jurisprudence_agent_uses_case_profile_for_a_non_uuid_case_id() -> None:
    """Sprint 42: `AgentInput.case_id` is `str | None` (was `uuid.UUID |
    None`), so a free-form case id like `"case-1"` (`CaseStorePort`'s own
    id format) now resolves the `CaseProfile`, instead of being silently
    lost to `None` for not parsing as a UUID."""
    case_store = InMemoryCaseStore()
    case_store.save(CaseProfile(case_id="case-1", title="Dupont c/ Acme"))

    agent = JurisprudenceAgent(orchestrator=_build_orchestrator(), case_store=case_store)
    agent_input = AgentInput(
        task_id=uuid.uuid4(),
        case_id="case-1",
        context={"query": "responsabilite contractuelle"},
    )

    output = await agent.run(agent_input)

    assert output.result["comparison"]
    assert not any("was not found in the case store" in warning for warning in output.warnings)


@pytest.mark.asyncio
async def test_jurisprudence_agent_warns_when_case_id_not_found() -> None:
    agent = JurisprudenceAgent(orchestrator=_build_orchestrator(), case_store=InMemoryCaseStore())
    missing_case_id = uuid.uuid4()
    agent_input = AgentInput(
        task_id=uuid.uuid4(),
        case_id=missing_case_id,
        context={"query": "responsabilite contractuelle"},
    )

    output = await agent.run(agent_input)

    assert any(str(missing_case_id) in warning for warning in output.warnings)


@pytest.mark.asyncio
async def test_jurisprudence_agent_passes_case_id_to_orchestrator_history() -> None:
    orchestrator = _build_orchestrator()
    agent = JurisprudenceAgent(orchestrator=orchestrator)
    case_id = str(uuid.uuid4())
    agent_input = AgentInput(
        task_id=uuid.uuid4(), case_id=case_id, context={"query": "responsabilite contractuelle"}
    )

    await agent.run(agent_input)

    entries = orchestrator.history.list_for_case(case_id)
    assert len(entries) == 1


@pytest.mark.asyncio
async def test_jurisprudence_agent_records_explainability_when_governance_is_wired() -> None:
    governance = _build_governance()
    agent = JurisprudenceAgent(
        orchestrator=_build_orchestrator(), governance=governance, firm_id="firm-x"
    )
    task_id = uuid.uuid4()
    agent_input = AgentInput(
        task_id=task_id, case_id=None, context={"query": "responsabilite contractuelle"}
    )

    await agent.run(agent_input)

    report = governance.explainability.latest("firm-x", str(task_id))
    assert report is not None
    assert "cass-civ1-2021" in report.documents_consulted
    assert any("Comparaison générée" in step for step in report.steps_followed)


@pytest.mark.asyncio
async def test_jurisprudence_agent_records_explainability_without_generation_when_empty() -> None:
    governance = _build_governance()
    agent = JurisprudenceAgent(
        orchestrator=_build_orchestrator(_EmptySearch()), governance=governance, firm_id="firm-x"
    )
    task_id = uuid.uuid4()
    agent_input = AgentInput(
        task_id=task_id, case_id=None, context={"query": "clause introuvable"}
    )

    await agent.run(agent_input)

    report = governance.explainability.latest("firm-x", str(task_id))
    assert report is not None
    assert not any("Comparaison générée" in step for step in report.steps_followed)
