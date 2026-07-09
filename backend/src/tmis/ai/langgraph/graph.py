from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from tmis.ai.langgraph.nodes import (
    make_analysis_node,
    make_orchestrator_node,
    make_research_node,
    make_response_node,
    make_user_question_node,
    make_verification_node,
)
from tmis.ai.langgraph.ports import KernelFacadePort
from tmis.ai.langgraph.state import KernelWorkflowState


def build_kernel_graph(kernel: KernelFacadePort) -> CompiledStateGraph:
    """Builds the Sprint 2 demo workflow:

    Utilisateur -> Orchestrateur -> Analyse -> Recherche -> Vérification -> Réponse

    `kernel` only needs to satisfy `KernelFacadePort`; no business logic
    lives here (see docs/11-langgraph-architecture.md).
    """
    graph = StateGraph(KernelWorkflowState)

    # Node names are suffixed with `_step` because LangGraph forbids a node
    # name that collides with a `KernelWorkflowState` key (e.g. "analysis").
    graph.add_node("user_question_step", make_user_question_node(kernel))
    graph.add_node("orchestrator_step", make_orchestrator_node(kernel))
    graph.add_node("analysis_step", make_analysis_node(kernel))
    graph.add_node("research_step", make_research_node(kernel))
    graph.add_node("verification_step", make_verification_node(kernel))
    graph.add_node("response_step", make_response_node(kernel))

    graph.set_entry_point("user_question_step")
    graph.add_edge("user_question_step", "orchestrator_step")
    graph.add_edge("orchestrator_step", "analysis_step")
    graph.add_edge("analysis_step", "research_step")
    graph.add_edge("research_step", "verification_step")
    graph.add_edge("verification_step", "response_step")
    graph.add_edge("response_step", END)

    return graph.compile()
