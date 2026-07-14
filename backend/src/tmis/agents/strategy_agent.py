from tmis.agents.contracts import AgentInput, AgentOutput


class StrategyAgent:
    """Pistes d'analyse et arguments favorables/défavorables (docs/05-strategie-multi-agents.md).

    Out of the current 41-sprint roadmap (docs/09-roadmap-30-sprints.md):
    the old Sprint 19 "Agent Stratégie" was absorbed by Sprint 6 (Legal
    Reasoning Engine's `strategy`/`hypotheses`/`validation` modules) and no
    longer exists as a dedicated sprint for wiring this agent. This
    Sprint 1 placeholder only establishes the AgentPort contract.
    """

    name = "strategy"

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        raise NotImplementedError(
            "StrategyAgent has no dedicated sprint in the current roadmap "
            "(see docs/09-roadmap-30-sprints.md)."
        )
