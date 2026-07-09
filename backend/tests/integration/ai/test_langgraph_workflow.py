import pytest

from tmis.ai.events.events import (
    ResearchCompleted,
    UserQuestionReceived,
    VerificationCompleted,
    WorkflowFinished,
    WorkflowStarted,
)
from tmis.ai.kernel import TMISKernel


@pytest.mark.asyncio
async def test_run_workflow_executes_all_five_nodes_in_order() -> None:
    kernel = TMISKernel()

    result = await kernel.run_workflow("kernel_demo", "dommage")

    assert result["response"] is not None
    assert result["analysis"] is not None
    assert isinstance(result["verification_warnings"], list)

    event_types = [type(e) for e in kernel.event_bus.history]
    assert event_types == [
        UserQuestionReceived,
        WorkflowStarted,
        ResearchCompleted,
        VerificationCompleted,
        WorkflowFinished,
    ]


@pytest.mark.asyncio
async def test_run_workflow_response_includes_matching_connector_sources() -> None:
    kernel = TMISKernel()

    result = await kernel.run_workflow("kernel_demo", "dommage")

    assert "Sources" in (result["response"] or "")


@pytest.mark.asyncio
async def test_run_workflow_unknown_name_raises() -> None:
    kernel = TMISKernel()
    with pytest.raises(ValueError, match="Unknown workflow"):
        await kernel.run_workflow("does-not-exist", "question")


@pytest.mark.asyncio
async def test_run_workflow_records_trace_in_workflow_memory() -> None:
    kernel = TMISKernel()

    result = await kernel.run_workflow("kernel_demo", "dommage")
    workflow_id = result["workflow_id"]

    trace = await kernel.workflow_memory.get_trace(workflow_id)
    assert any("workflow_finished" in step for step in trace)
