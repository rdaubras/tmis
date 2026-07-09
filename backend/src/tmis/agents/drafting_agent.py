from tmis.agents.contracts import AgentInput, AgentOutput


class DraftingAgent:
    """Génération de brouillons de documents juridiques (docs/05-strategie-multi-agents.md).

    Implementation is scheduled for Sprint 18
    (see docs/09-roadmap-30-sprints.md). This Sprint 1 placeholder only
    establishes the AgentPort contract.
    """

    name = "drafting"

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        raise NotImplementedError(
            "DraftingAgent is scheduled for Sprint 18 (see docs/09-roadmap-30-sprints.md)."
        )
