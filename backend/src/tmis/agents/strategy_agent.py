from tmis.agents.contracts import AgentInput, AgentOutput


class StrategyAgent:
    """Pistes d'analyse et arguments favorables/défavorables (docs/05-strategie-multi-agents.md).

    Implementation is scheduled for Sprint 19
    (see docs/09-roadmap-30-sprints.md). This Sprint 1 placeholder only
    establishes the AgentPort contract.
    """

    name = "strategy"

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        raise NotImplementedError(
            "StrategyAgent is scheduled for Sprint 19 (see docs/09-roadmap-30-sprints.md)."
        )
