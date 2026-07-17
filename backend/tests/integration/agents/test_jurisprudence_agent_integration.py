"""End-to-end: a query flows through the real `ResearchOrchestrator` (Sprint
5, the LRE, via its own `get_shared_research_orchestrator()` bootstrap — codes/
jurisprudence/doctrine connectors plus the LRE's internal documentation and
private database connectors), filtered to the "jurisprudence" connector, and
comes back out through the real `JurisprudenceAgent` (Sprint 34) with its
`ResearchCitation`s converted to the agents contract's `Citation` and a
generative comparison produced through the real `TMISKernel.complete()`."""

import uuid

import pytest

from tmis.agents.contracts import AgentInput, ConfidenceLevel
from tmis.agents.jurisprudence_agent import JurisprudenceAgent
from tmis.ai.kernel.bootstrap import get_kernel
from tmis.legal_research.bootstrap import clear_research_caches, get_shared_research_orchestrator


@pytest.fixture(autouse=True)
def _clear_singletons() -> None:
    """Same reset as `test_research_agent_integration.py`: both are
    `lru_cache`d process-wide singletons that must not leak connector
    registrations or history between tests."""
    clear_research_caches()
    get_kernel.cache_clear()


@pytest.mark.asyncio
async def test_query_flows_through_the_real_lre_filtered_to_jurisprudence() -> None:
    orchestrator = get_shared_research_orchestrator()
    agent = JurisprudenceAgent(orchestrator=orchestrator)

    task_id = uuid.uuid4()
    agent_input = AgentInput(
        task_id=task_id,
        case_id=None,
        context={"query": "responsabilité contractuelle"},
    )

    output = await agent.run(agent_input)

    assert output.result["results"]
    assert output.result["query"] == "responsabilité contractuelle"
    assert output.confidence in (ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH)
    assert output.result["comparison"]

    # Every result and citation comes from the "jurisprudence" connector
    # only — no second search engine, no unfiltered fan-out.
    for result in output.result["results"]:
        assert result["connector"] == "jurisprudence"
    assert len(output.citations) == len(output.result["results"])
    for citation in output.citations:
        assert citation.connector == "jurisprudence"
        assert citation.source_id
        assert citation.reference


@pytest.mark.asyncio
async def test_agent_forwards_case_id_to_the_orchestrator_history() -> None:
    orchestrator = get_shared_research_orchestrator()
    agent = JurisprudenceAgent(orchestrator=orchestrator)
    case_id = str(uuid.uuid4())

    agent_input = AgentInput(
        task_id=uuid.uuid4(),
        case_id=case_id,
        context={"query": "clause de non-concurrence"},
    )

    await agent.run(agent_input)

    entries = orchestrator.history.list_for_case(case_id)
    assert len(entries) == 1
    assert entries[0].query_text == "clause de non-concurrence"


@pytest.mark.asyncio
async def test_agent_reports_low_confidence_and_no_search_when_query_is_missing() -> None:
    agent = JurisprudenceAgent(orchestrator=get_shared_research_orchestrator())
    agent_input = AgentInput(task_id=uuid.uuid4(), case_id=None)

    output = await agent.run(agent_input)

    assert output.confidence == ConfidenceLevel.LOW
    assert output.result["results"] == []
    assert output.result["comparison"] is None
    assert output.citations == []
