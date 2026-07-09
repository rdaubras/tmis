from tmis.agents.contracts import AgentInput, AgentOutput


class ResearchAgent:
    """Recherche documentaire via connecteurs configurables (docs/05-strategie-multi-agents.md).

    Implementation is scheduled for Sprint 15
    (see docs/09-roadmap-30-sprints.md). This Sprint 1 placeholder only
    establishes the AgentPort contract.
    """

    name = "research"

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        raise NotImplementedError(
            "ResearchAgent is scheduled for Sprint 15 (see docs/09-roadmap-30-sprints.md)."
        )
