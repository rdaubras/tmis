from tmis.agents.contracts import AgentInput, AgentOutput


class ContractAgent:
    """Analyse et comparaison de contrats (docs/05-strategie-multi-agents.md).

    Implementation is scheduled for Sprint 17
    (see docs/09-roadmap-30-sprints.md). This Sprint 1 placeholder only
    establishes the AgentPort contract.
    """

    name = "contract"

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        raise NotImplementedError(
            "ContractAgent is scheduled for Sprint 17 (see docs/09-roadmap-30-sprints.md)."
        )
