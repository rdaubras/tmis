from tmis.agents.contracts import AgentInput, AgentOutput


class CollaborationAgent:
    """Historique, commentaires, validation, versionning (docs/05-strategie-multi-agents.md).

    Out of the current 41-sprint roadmap (docs/09-roadmap-30-sprints.md):
    the old Sprint 20 "Agent Collaboration" was absorbed by Sprint 8 (Legal
    Collaboration Engine, `tmis.collaboration`) and no longer exists as a
    dedicated sprint for wiring this agent. This Sprint 1 placeholder only
    establishes the AgentPort contract.
    """

    name = "collaboration"

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        raise NotImplementedError(
            "CollaborationAgent has no dedicated sprint in the current roadmap "
            "(see docs/09-roadmap-30-sprints.md)."
        )
