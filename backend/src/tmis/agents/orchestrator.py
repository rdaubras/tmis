from typing import TypedDict, cast

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from tmis.agents.analysis_agent import AnalysisAgent
from tmis.agents.contracts import AgentInput, AgentOutput
from tmis.agents.synthesis_agent import SynthesisAgent
from tmis.agents.verifier_agent import VerifierAgent


class OrchestratorState(TypedDict):
    agent_input: AgentInput
    output: AgentOutput | None


def _fuse_with_synthesis(previous: AgentOutput, synthesis: AgentOutput) -> AgentOutput:
    """Merges the Synthesis node's deliverables into the verified output
    rather than replacing it: `previous.confidence` (the Verifier's
    assessment of the primary result's trustworthiness) is kept as-is,
    since Synthesis answers a different question ("what does the case
    look like as a whole?") that can legitimately have nothing to add
    (no `case_id`, or a case not yet in the store) without that being a
    quality problem with what `previous` already established."""
    return AgentOutput(
        result={**previous.result, "synthesis": synthesis.result},
        citations=[*previous.citations, *synthesis.citations],
        confidence=previous.confidence,
        warnings=[*previous.warnings, *synthesis.warnings],
    )


class Orchestrator:
    """Chef d'Orchestre: splits a request, routes it to specialized agents,
    always passes sensitive output through the Verifier, then fuses the
    final response (see docs/05-strategie-multi-agents.md).

    Sprint 1 wired a single demonstrative path (analysis -> verifier) to
    prove the LangGraph plumbing end-to-end. Sprint 29 made that path real
    — "analysis" now runs the real `AnalysisAgent` (`TMISKernel.complete()`,
    `DocumentStorePort`/`CaseStorePort`, `AIIntelligenceFabric`,
    `AIGovernancePlatform` — see docs/157-architecture-agent-analyse.md) —
    without changing this class's wiring: the constructor already accepted
    an injectable `analysis_agent` for exactly this reason.

    Sprint 30 adds a third node, "synthesis", between "verifier" and `END`
    — the real `SynthesisAgent` (`CaseStorePort`/`CaseSummaryGenerator`,
    `WritingStyleEngine`, `AIIntelligenceFabric`, `AIGovernancePlatform` —
    see docs/158-architecture-agent-synthese.md). Unlike the Verifier,
    Synthesis is a plain `AgentPort` (it implements `run(agent_input)`,
    not a `.verify(output)` post-processor), so `run_synthesis` calls
    `self._synthesis_agent.run(state["agent_input"])` exactly like
    `run_analysis` does. Its result is *merged* into the verified output
    (`_fuse_with_synthesis`) rather than replacing it — `OrchestratorState`
    only ever holds one `AgentOutput`, and Synthesis answers a different
    question ("what does the whole case look like?") than Analysis/Verifier
    do, so its confidence never overrides the Verifier's assessment of the
    primary result; its `result`, `citations` and `warnings` are appended
    under a `"synthesis"` key instead of overwriting anything Analysis
    produced. This is the one place this sprint's "exactly the documented
    pattern" instruction had to be read as "closure + injectable
    constructor param + edges", not "literally return the new agent's
    output verbatim" — see docs/reports/sprint-30-rapport-architecture.md
    for why a verbatim replacement would have broken the existing
    Sprint 29 tests.

    **Pattern for a future agent (Sprint 31 and later)** — add a node to
    the same graph without changing this contract:

    1. Add a constructor parameter for the new agent (e.g.
       `verifier_agent` already does this), defaulting to its own
       placeholder/real implementation the same way `analysis_agent`,
       `verifier_agent` and `synthesis_agent` already do.
    2. In `_build_graph`, add one `async def run_<name>(state)` closure that
       calls `self._<name>_agent.run(state["agent_input"])` (or, for a
       post-processing agent like the Verifier, `.verify(state["output"])`
       on the previous node's output) and returns `{**state, "output":
       output}` — or, if the new node should *add to* rather than replace
       what came before (as Synthesis does), fuse it into the previous
       output the same way `_fuse_with_synthesis` does, rather than
       silently discarding upstream results.
    3. Register it with `graph.add_node(...)` and wire its edges — a new
       agent that runs *instead of* or *before* Analysis changes the entry
       point/edges; one that runs *after* Synthesis is inserted between
       `"synthesis"` and `END`.
    4. Every agent in the graph still only implements `AgentPort`
       (`name` + `async def run(agent_input) -> AgentOutput`, see
       `tmis.agents.contracts`) — so `OrchestratorState` and the public
       `Orchestrator.run()` method never need to change.
    """

    def __init__(
        self,
        analysis_agent: AnalysisAgent | None = None,
        verifier_agent: VerifierAgent | None = None,
        synthesis_agent: SynthesisAgent | None = None,
    ) -> None:
        self._analysis_agent = analysis_agent or AnalysisAgent()
        self._verifier_agent = verifier_agent or VerifierAgent()
        self._synthesis_agent = synthesis_agent or SynthesisAgent()
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

        async def run_synthesis(state: OrchestratorState) -> OrchestratorState:
            assert state["output"] is not None
            synthesis_output = await self._synthesis_agent.run(state["agent_input"])
            fused = _fuse_with_synthesis(state["output"], synthesis_output)
            return {**state, "output": fused}

        graph.add_node("analysis", run_analysis)
        graph.add_node("verifier", run_verifier)
        graph.add_node("synthesis", run_synthesis)
        graph.set_entry_point("analysis")
        graph.add_edge("analysis", "verifier")
        graph.add_edge("verifier", "synthesis")
        graph.add_edge("synthesis", END)
        return graph.compile()

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        final_state = await self._graph.ainvoke({"agent_input": agent_input, "output": None})
        output = cast(OrchestratorState, final_state)["output"]
        assert output is not None
        return output
