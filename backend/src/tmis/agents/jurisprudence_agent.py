from tmis.agents.contracts import AgentInput, AgentOutput


class JurisprudenceAgent:
    """Recherche et comparaison de jurisprudence (docs/05-strategie-multi-agents.md).

    Implementation is scheduled for Sprint 34
    (see docs/09-roadmap-30-sprints.md). This Sprint 1 placeholder only
    establishes the AgentPort contract.
    """

    name = "jurisprudence"

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        raise NotImplementedError(
            "JurisprudenceAgent is scheduled for Sprint 34 (see docs/09-roadmap-30-sprints.md)."
        )
