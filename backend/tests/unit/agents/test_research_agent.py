import uuid

import pytest

from tmis.agents.contracts import AgentInput, ConfidenceLevel
from tmis.agents.research_agent import ResearchAgent
from tmis.ai.cache.in_memory_cache import InMemoryCache
from tmis.ai.schemas.connector import ConnectorDocument
from tmis.ai_governance.explainability.engine import ExplainabilityEngine
from tmis.ai_governance.explainability.store import InMemoryExplainabilityStore
from tmis.ai_governance.overview import AIGovernancePlatform
from tmis.legal_research.cache.research_cache import ResearchCache
from tmis.legal_research.citations.engine import CitationEngine
from tmis.legal_research.evaluation.evaluator import ResearchEvaluator
from tmis.legal_research.history.in_memory_history import InMemoryResearchHistory
from tmis.legal_research.normalization.normalizer import SourceNormalizer
from tmis.legal_research.queries.engine import HeuristicQueryEngine
from tmis.legal_research.queries.schemas import ResearchQuery
from tmis.legal_research.ranking.configurable_ranker import ConfigurableRanker
from tmis.legal_research.search.orchestrator import ResearchOrchestrator
from tmis.legal_research.search.schemas import RelevanceScores
from tmis.legal_research.sources.registry import SourceRegistry

_DOCS = [
    ConnectorDocument(
        id="civ-1240",
        title="Code civil, article 1240",
        content="Tout fait quelconque de l'homme, qui cause a autrui un dommage.",
        connector="codes",
        metadata={"article": "1240", "date": "1804-01-01"},
    ),
    ConnectorDocument(
        id="doctrine-1",
        title="Chronique responsabilite",
        content="Analyse doctrinale du dommage et de la responsabilite.",
        connector="doctrine",
        metadata={"date": "2020-01-01"},
    ),
]


class _FakeSearch:
    async def execute(
        self, query: ResearchQuery, *, connector_names: list[str] | None = None
    ) -> tuple[list[ConnectorDocument], list[str], dict[str, RelevanceScores]]:
        scores = {
            "civ-1240": RelevanceScores(lexical_score=0.9, vector_score=0.8),
            "doctrine-1": RelevanceScores(lexical_score=0.2, vector_score=0.3),
        }
        return list(_DOCS), ["codes", "doctrine"], scores


def _build_orchestrator() -> ResearchOrchestrator:
    return ResearchOrchestrator(
        query_engine=HeuristicQueryEngine(),
        search=_FakeSearch(),
        normalizer=SourceNormalizer(),
        ranker=ConfigurableRanker(SourceRegistry(), current_year_fn=lambda: 2026),
        citation_engine=CitationEngine(),
        cache=ResearchCache(InMemoryCache()),
        history=InMemoryResearchHistory(),
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
async def test_research_agent_without_query_is_low_confidence() -> None:
    agent = ResearchAgent(orchestrator=_build_orchestrator())
    agent_input = AgentInput(task_id=uuid.uuid4(), case_id=None)

    output = await agent.run(agent_input)

    assert output.confidence == ConfidenceLevel.LOW
    assert output.result["results"] == []
    assert any("No query" in warning for warning in output.warnings)


class _EmptySearch:
    async def execute(
        self, query: ResearchQuery, *, connector_names: list[str] | None = None
    ) -> tuple[list[ConnectorDocument], list[str], dict[str, RelevanceScores]]:
        return [], [], {}


@pytest.mark.asyncio
async def test_research_agent_reports_low_confidence_when_the_lre_finds_nothing() -> None:
    orchestrator = ResearchOrchestrator(
        query_engine=HeuristicQueryEngine(),
        search=_EmptySearch(),
        normalizer=SourceNormalizer(),
        ranker=ConfigurableRanker(SourceRegistry(), current_year_fn=lambda: 2026),
        citation_engine=CitationEngine(),
        cache=ResearchCache(InMemoryCache()),
        history=InMemoryResearchHistory(),
        evaluator=ResearchEvaluator(),
    )
    agent = ResearchAgent(orchestrator=orchestrator)
    agent_input = AgentInput(
        task_id=uuid.uuid4(), case_id=None, context={"query": "une question introuvable"}
    )

    output = await agent.run(agent_input)

    assert output.confidence == ConfidenceLevel.LOW
    assert output.result["results"] == []
    assert output.citations == []
    assert any("No result found" in warning for warning in output.warnings)


@pytest.mark.asyncio
async def test_research_agent_runs_a_real_search_and_converts_citations() -> None:
    agent = ResearchAgent(orchestrator=_build_orchestrator())
    task_id = uuid.uuid4()
    agent_input = AgentInput(
        task_id=task_id, case_id=None, context={"query": "responsabilite civile"}
    )

    output = await agent.run(agent_input)

    assert output.confidence == ConfidenceLevel.MEDIUM
    results = output.result["results"]
    assert isinstance(results, list)
    assert len(results) == 2
    assert output.result["query"] == "responsabilite civile"
    assert output.result["cache_hit"] is False

    assert len(output.citations) == 2
    connectors = {citation.connector for citation in output.citations}
    assert connectors == {"codes", "doctrine"}
    for citation in output.citations:
        assert citation.excerpt
        assert citation.reference
        assert citation.source_id


@pytest.mark.asyncio
async def test_research_agent_cache_hit_raises_confidence_to_high() -> None:
    orchestrator = _build_orchestrator()
    agent = ResearchAgent(orchestrator=orchestrator)
    agent_input = AgentInput(
        task_id=uuid.uuid4(), case_id=None, context={"query": "responsabilite civile"}
    )

    await agent.run(agent_input)
    second = await agent.run(agent_input)

    assert second.result["cache_hit"] is True
    assert second.confidence == ConfidenceLevel.HIGH


@pytest.mark.asyncio
async def test_research_agent_passes_case_id_to_orchestrator_history() -> None:
    orchestrator = _build_orchestrator()
    agent = ResearchAgent(orchestrator=orchestrator)
    case_id = str(uuid.uuid4())
    agent_input = AgentInput(
        task_id=uuid.uuid4(), case_id=case_id, context={"query": "responsabilite civile"}
    )

    await agent.run(agent_input)

    entries = orchestrator.history.list_for_case(case_id)
    assert len(entries) == 1


@pytest.mark.asyncio
async def test_research_agent_passes_a_non_uuid_case_id_to_orchestrator_history() -> None:
    """Sprint 42: `AgentInput.case_id` is `str | None` (was `uuid.UUID |
    None`), so a free-form case id like `"case-1"` (`CaseStorePort`'s own
    id format) now reaches `ResearchOrchestrator.search()` as-is, instead
    of being silently lost to `None` for not parsing as a UUID."""
    orchestrator = _build_orchestrator()
    agent = ResearchAgent(orchestrator=orchestrator)
    agent_input = AgentInput(
        task_id=uuid.uuid4(), case_id="case-1", context={"query": "responsabilite civile"}
    )

    await agent.run(agent_input)

    entries = orchestrator.history.list_for_case("case-1")
    assert len(entries) == 1


@pytest.mark.asyncio
async def test_research_agent_records_explainability_when_governance_is_wired() -> None:
    governance = _build_governance()
    agent = ResearchAgent(
        orchestrator=_build_orchestrator(), governance=governance, firm_id="firm-x"
    )
    task_id = uuid.uuid4()
    agent_input = AgentInput(
        task_id=task_id, case_id=None, context={"query": "responsabilite civile"}
    )

    await agent.run(agent_input)

    report = governance.explainability.latest("firm-x", str(task_id))
    assert report is not None
    assert "civ-1240" in report.documents_consulted
