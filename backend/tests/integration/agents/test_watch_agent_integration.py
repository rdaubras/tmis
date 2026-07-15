"""End-to-end: a watch configuration flows through the real
`ResearchOrchestrator` (Sprint 5, the LRE, via its own
`get_research_orchestrator()` bootstrap) and comes back out through the real
`WatchAgent` (Sprint 36) with its `ResearchCitation`s converted to the agents
contract's `Citation` and an alert synthesized through the real
`TMISKernel.complete()` — never a second search engine, never a second
generative call site."""

import uuid

import pytest

from tmis.agents.contracts import AgentInput, ConfidenceLevel
from tmis.agents.watch_agent import WatchAgent
from tmis.ai.kernel.bootstrap import get_kernel
from tmis.legal_research.bootstrap import get_research_orchestrator


@pytest.fixture(autouse=True)
def _clear_singletons() -> None:
    """Same reset as `test_jurisprudence_agent_integration.py`: both are
    `lru_cache`d process-wide singletons that must not leak connector
    registrations or history between tests."""
    get_research_orchestrator.cache_clear()
    get_kernel.cache_clear()


@pytest.mark.asyncio
async def test_first_watch_run_reports_every_result_as_new() -> None:
    orchestrator = get_research_orchestrator()
    agent = WatchAgent(orchestrator=orchestrator)

    task_id = uuid.uuid4()
    agent_input = AgentInput(
        task_id=task_id,
        case_id=None,
        context={"query": "responsabilité contractuelle", "connectors": ["jurisprudence"]},
    )

    output = await agent.run(agent_input)

    assert output.result["query"] == "responsabilité contractuelle"
    assert output.confidence in (ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH)
    new_results = output.result["new_results"]
    assert new_results
    assert output.result["alert_message"]

    # Every result and citation comes from the "jurisprudence" connector
    # only — no second search engine, no unfiltered fan-out.
    for result in new_results:
        assert result["connector"] == "jurisprudence"
    assert len(output.citations) == len(new_results)
    for citation in output.citations:
        assert citation.connector == "jurisprudence"
        assert citation.source_id
        assert citation.reference


@pytest.mark.asyncio
async def test_a_second_run_with_the_first_runs_ids_reports_no_new_result() -> None:
    orchestrator = get_research_orchestrator()
    agent = WatchAgent(orchestrator=orchestrator)

    first_input = AgentInput(
        task_id=uuid.uuid4(),
        case_id=None,
        context={"query": "responsabilité contractuelle", "connectors": ["jurisprudence"]},
    )
    first_output = await agent.run(first_input)
    known_ids = first_output.result["result_ids"]
    assert known_ids

    second_input = AgentInput(
        task_id=uuid.uuid4(),
        case_id=None,
        context={
            "query": "responsabilité contractuelle",
            "connectors": ["jurisprudence"],
            "known_result_ids": known_ids,
        },
    )
    second_output = await agent.run(second_input)

    assert second_output.result["new_results"] == []
    assert second_output.result["alert_message"] is None
    assert second_output.citations == []
    assert any("No new result" in warning for warning in second_output.warnings)


@pytest.mark.asyncio
async def test_agent_forwards_case_id_to_the_orchestrator_history() -> None:
    orchestrator = get_research_orchestrator()
    agent = WatchAgent(orchestrator=orchestrator)
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
    agent = WatchAgent(orchestrator=get_research_orchestrator())
    agent_input = AgentInput(task_id=uuid.uuid4(), case_id=None)

    output = await agent.run(agent_input)

    assert output.confidence == ConfidenceLevel.LOW
    assert output.result["new_results"] == []
    assert output.citations == []
