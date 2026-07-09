from tmis.agents.contracts import AgentInput, AgentOutput


class WatchAgent:
    """Veille juridique et génération d'alertes (docs/05-strategie-multi-agents.md).

    Implementation is scheduled for Sprint 21
    (see docs/09-roadmap-30-sprints.md). This Sprint 1 placeholder only
    establishes the AgentPort contract.
    """

    name = "watch"

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        raise NotImplementedError(
            "WatchAgent is scheduled for Sprint 21 (see docs/09-roadmap-30-sprints.md)."
        )
