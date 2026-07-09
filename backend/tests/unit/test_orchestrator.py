import uuid

import pytest

from tmis.agents.contracts import AgentInput, ConfidenceLevel
from tmis.agents.orchestrator import Orchestrator
from tmis.agents.verifier_agent import VerifierAgent
from tmis.ai.schemas.citation import Citation


@pytest.mark.asyncio
async def test_orchestrator_runs_analysis_then_verifier() -> None:
    orchestrator = Orchestrator()
    agent_input = AgentInput(task_id=uuid.uuid4(), case_id=uuid.uuid4())

    output = await orchestrator.run(agent_input)

    assert output.confidence == ConfidenceLevel.LOW
    assert any("placeholder" in warning for warning in output.warnings)


@pytest.mark.asyncio
async def test_verifier_flags_incomplete_citations() -> None:
    from tmis.agents.contracts import AgentOutput

    verifier = VerifierAgent()
    output = AgentOutput(
        result={},
        citations=[Citation(source_id="doc-1", connector="codes", excerpt="", reference="")],
        confidence=ConfidenceLevel.HIGH,
    )

    verified = await verifier.verify(output)

    assert verified.confidence == ConfidenceLevel.MEDIUM
    assert any("traceable" in warning for warning in verified.warnings)
