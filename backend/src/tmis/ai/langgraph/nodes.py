from collections.abc import Awaitable, Callable

from tmis.ai.events.events import (
    ResearchCompleted,
    UserQuestionReceived,
    VerificationCompleted,
    WorkflowStarted,
)
from tmis.ai.langgraph.ports import KernelFacadePort
from tmis.ai.langgraph.state import KernelWorkflowState
from tmis.ai.schemas.agent import AgentOutput, ConfidenceLevel

NodeFn = Callable[[KernelWorkflowState], Awaitable[KernelWorkflowState]]

WORKFLOW_NAME = "kernel_demo"


def make_user_question_node(kernel: KernelFacadePort) -> NodeFn:
    async def node(state: KernelWorkflowState) -> KernelWorkflowState:
        await kernel.publish_event(
            UserQuestionReceived(workflow_id=state["workflow_id"], question=state["question"])
        )
        return state

    return node


def make_orchestrator_node(kernel: KernelFacadePort) -> NodeFn:
    async def node(state: KernelWorkflowState) -> KernelWorkflowState:
        await kernel.publish_event(
            WorkflowStarted(workflow_id=state["workflow_id"], workflow_name=WORKFLOW_NAME)
        )
        return state

    return node


def make_analysis_node(kernel: KernelFacadePort) -> NodeFn:
    async def node(state: KernelWorkflowState) -> KernelWorkflowState:
        response = await kernel.complete(f"Analyse: {state['question']}")
        analysis = AgentOutput(
            result={"analysis": response.text},
            confidence=ConfidenceLevel.MEDIUM,
        )
        return {**state, "analysis": analysis}

    return node


def make_research_node(kernel: KernelFacadePort) -> NodeFn:
    async def node(state: KernelWorkflowState) -> KernelWorkflowState:
        documents = await kernel.search_connectors(state["question"])
        await kernel.publish_event(
            ResearchCompleted(workflow_id=state["workflow_id"], result_count=len(documents))
        )
        return {**state, "research": documents}

    return node


def make_verification_node(kernel: KernelFacadePort) -> NodeFn:
    async def node(state: KernelWorkflowState) -> KernelWorkflowState:
        analysis = state["analysis"]
        warnings = kernel.validate_output(analysis) if analysis is not None else []
        await kernel.publish_event(
            VerificationCompleted(workflow_id=state["workflow_id"], warning_count=len(warnings))
        )
        return {**state, "verification_warnings": warnings}

    return node


def make_response_node(kernel: KernelFacadePort) -> NodeFn:
    async def node(state: KernelWorkflowState) -> KernelWorkflowState:
        analysis = state["analysis"]
        analysis_text = str(analysis.result.get("analysis", "")) if analysis else ""
        sources = ", ".join(doc.title for doc in state["research"])
        response = f"{analysis_text}\n\nSources : {sources}" if sources else analysis_text
        return {**state, "response": response}

    return node
