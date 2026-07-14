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

    Sprint 1 wired a single demonstrative path (analysis -> verifier) to
    prove the LangGraph plumbing end-to-end. Sprint 29 makes that path real
    — "analysis" now runs the real `AnalysisAgent` (`TMISKernel.complete()`,
    `DocumentStorePort`/`CaseStorePort`, `AIIntelligenceFabric`,
    `AIGovernancePlatform` — see docs/157-architecture-agent-analyse.md) —
    without changing this class's wiring: the constructor already accepted
    an injectable `analysis_agent` for exactly this reason.

    **Pattern for a future agent (Sprint 30 and later)** — add a node to
    the same graph without changing this contract:

    1. Add a constructor parameter for the new agent (e.g.
       `synthesis_agent: SynthesisAgent | None = None`), defaulting to its
       own placeholder/real implementation the same way `analysis_agent`
       and `verifier_agent` already do.
    2. In `_build_graph`, add one `async def run_<name>(state)` closure that
       calls `self._<name>_agent.run(state["agent_input"])` (or, for a
       post-processing agent like the Verifier, `.verify(state["output"])`
       on the previous node's output) and returns `{**state, "output":
       output}`.
    3. Register it with `graph.add_node(...)` and wire its edges — a new
       agent that runs *instead of* or *before* Analysis changes the entry
       point/edges; one that runs *after* Verifier (e.g. Synthesis
       consuming the verified output) is inserted between `"verifier"` and
       `END`.
    4. Every agent in the graph still only implements `AgentPort`
       (`name` + `async def run(agent_input) -> AgentOutput`, see
       `tmis.agents.contracts`) — the same contract this Sprint 29 sprint
       exercises end-to-end for the first time — so `OrchestratorState`
       and the public `Orchestrator.run()` method never need to change.
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
