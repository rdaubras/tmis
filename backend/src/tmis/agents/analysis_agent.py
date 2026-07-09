from tmis.agents.contracts import AgentInput, AgentOutput, ConfidenceLevel


class AnalysisAgent:
    """Entity/fact extraction and inconsistency detection (docs/05).

    Full extraction logic (persons, companies, facts, dates, contracts,
    events, jurisdictions, amounts) is implemented in a future sprint
    (see docs/09-roadmap-30-sprints.md, Sprint 11). This Sprint 1 version
    returns an empty, clearly low-confidence result so the orchestrator
    graph is exercisable end-to-end today.
    """

    name = "analysis"

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        return AgentOutput(
            result={"entities": [], "inconsistencies": []},
            confidence=ConfidenceLevel.LOW,
            warnings=["Analysis agent is a Sprint 1 placeholder: no extraction performed yet."],
        )
