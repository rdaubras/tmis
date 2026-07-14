from tmis.agents.contracts import AgentInput, AgentOutput


class DraftingAgent:
    """Génération de brouillons de documents juridiques (docs/05-strategie-multi-agents.md).

    Out of the current 41-sprint roadmap (docs/09-roadmap-30-sprints.md):
    the underlying drafting engine already exists (`tmis.legal_drafting`,
    Sprint 7), and no dedicated future sprint wires an agent on top of it
    (Phase 3 of the roadmap, Sprints 29-36, does not list a drafting
    agent) — same situation as `StrategyAgent`/`CollaborationAgent` below.
    This Sprint 1 placeholder only establishes the AgentPort contract.
    """

    name = "drafting"

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        raise NotImplementedError(
            "DraftingAgent has no dedicated sprint in the current roadmap "
            "(see docs/09-roadmap-30-sprints.md)."
        )
