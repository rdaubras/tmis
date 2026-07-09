from tmis.agents.contracts import AgentInput, AgentOutput


class SynthesisAgent:
    """Chronologies, résumés, tableaux, fiches, checklists (docs/05-strategie-multi-agents.md).

    Implementation is scheduled for Sprint 12
    (see docs/09-roadmap-30-sprints.md). This Sprint 1 placeholder only
    establishes the AgentPort contract.
    """

    name = "synthesis"

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        raise NotImplementedError(
            "SynthesisAgent is scheduled for Sprint 12 (see docs/09-roadmap-30-sprints.md)."
        )
