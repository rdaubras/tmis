from tmis.agents.contracts import AgentInput, AgentOutput


class CollaborationAgent:
    """Historique, commentaires, validation, versionning (docs/05-strategie-multi-agents.md).

    Implementation is scheduled for Sprint 20
    (see docs/09-roadmap-30-sprints.md). This Sprint 1 placeholder only
    establishes the AgentPort contract.
    """

    name = "collaboration"

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        raise NotImplementedError(
            "CollaborationAgent is scheduled for Sprint 20 (see docs/09-roadmap-30-sprints.md)."
        )
