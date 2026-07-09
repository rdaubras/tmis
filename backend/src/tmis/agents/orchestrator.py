from typing import TypedDict, cast

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from tmis.agents.analysis_agent import AnalysisAgent
from tmis.agents.contracts import AgentInput, AgentOutput
from tmis.agents.verifier_agent import VerifierAgent


class OrchestratorState(TypedDict):
    agent_input: AgentInput
    output: AgentOutput | None


class Orchestrator:
    """Chef d'Orchestre: splits a request, routes it to specialized agents,
    always passes sensitive output through the Verifier, then fuses the
    final response (see docs/05-strategie-multi-agents.md).

    Sprint 1 wires a single demonstrative path (analysis -> verifier) to
    prove the LangGraph plumbing end-to-end. Additional agents are plugged
    into the same graph in later sprints without changing this contract.
    """

    def __init__(
        self,
        analysis_agent: AnalysisAgent | None = None,
        verifier_agent: VerifierAgent | None = None,
    ) -> None:
        self._analysis_agent = analysis_agent or AnalysisAgent()
        self._verifier_agent = verifier_agent or VerifierAgent()
        self._graph = self._build_graph()

    def _build_graph(self) -> CompiledStateGraph:
        graph = StateGraph(OrchestratorState)

        async def run_analysis(state: OrchestratorState) -> OrchestratorState:
            output = await self._analysis_agent.run(state["agent_input"])
            return {**state, "output": output}

        async def run_verifier(state: OrchestratorState) -> OrchestratorState:
            assert state["output"] is not None
            verified = await self._verifier_agent.verify(state["output"])
            return {**state, "output": verified}

        graph.add_node("analysis", run_analysis)
        graph.add_node("verifier", run_verifier)
        graph.set_entry_point("analysis")
        graph.add_edge("analysis", "verifier")
        graph.add_edge("verifier", END)
        return graph.compile()

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        final_state = await self._graph.ainvoke({"agent_input": agent_input, "output": None})
        output = cast(OrchestratorState, final_state)["output"]
        assert output is not None
        return output
