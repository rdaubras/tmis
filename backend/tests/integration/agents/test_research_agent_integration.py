"""End-to-end: a query flows through the real `ResearchOrchestrator` (Sprint
5, the LRE, via its own `get_shared_research_orchestrator()` bootstrap — codes/
jurisprudence/doctrine connectors plus the LRE's internal documentation and
private database connectors) and comes back out through the real
`ResearchAgent` (Sprint 33) with its `ResearchCitation`s converted to the
agents contract's `Citation`."""

import uuid

import pytest

from tmis.agents.contracts import AgentInput, ConfidenceLevel
from tmis.agents.research_agent import ResearchAgent
from tmis.ai.kernel.bootstrap import get_kernel
from tmis.legal_research.bootstrap import clear_research_caches, get_shared_research_orchestrator


@pytest.fixture(autouse=True)
def _clear_singletons() -> None:
    """Same reset as `test_research_orchestrator_integration.py`: both are
    `lru_cache`d process-wide singletons that must not leak connector
    registrations or history between tests."""
    clear_research_caches()
    get_kernel.cache_clear()


@pytest.mark.asyncio
async def test_query_flows_through_the_real_lre_and_agent_converts_citations() -> None:
    orchestrator = get_shared_research_orchestrator()
    agent = ResearchAgent(orchestrator=orchestrator)

    task_id = uuid.uuid4()
    agent_input = AgentInput(
        task_id=task_id,
        case_id=None,
        context={"query": "contrat de travail"},
    )

    output = await agent.run(agent_input)

    assert output.result["results"]
    assert output.result["query"] == "contrat de travail"
    assert output.confidence in (ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH)

    # Every citation is a real `tmis.ai.schemas.citation.Citation`, converted
    # from the LRE's own `ResearchCitation` — not a second, parallel schema.
    assert len(output.citations) == len(output.result["results"])
    for citation in output.citations:
        assert citation.source_id
        assert citation.connector
        assert citation.reference
        assert not output.warnings or "No result" not in output.warnings[0]


@pytest.mark.asyncio
async def test_agent_forwards_case_id_to_the_orchestrator_history() -> None:
    orchestrator = get_shared_research_orchestrator()
    agent = ResearchAgent(orchestrator=orchestrator)
    case_id = str(uuid.uuid4())

    agent_input = AgentInput(
        task_id=uuid.uuid4(),
        case_id=case_id,
        context={"query": "non-concurrence"},
    )

    await agent.run(agent_input)

    entries = orchestrator.history.list_for_case(case_id)
    assert len(entries) == 1
    assert entries[0].query_text == "non-concurrence"


@pytest.mark.asyncio
async def test_agent_reports_low_confidence_and_no_search_when_query_is_missing() -> None:
    agent = ResearchAgent(orchestrator=get_shared_research_orchestrator())
    agent_input = AgentInput(task_id=uuid.uuid4(), case_id=None)

    output = await agent.run(agent_input)

    assert output.confidence == ConfidenceLevel.LOW
    assert output.result["results"] == []
    assert output.citations == []
