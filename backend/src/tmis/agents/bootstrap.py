from functools import lru_cache

from tmis.agents.research_agent import ResearchAgent
from tmis.ai_governance.bootstrap import get_ai_governance_platform
from tmis.legal_research.bootstrap import get_research_orchestrator


@lru_cache
def get_research_agent() -> ResearchAgent:
    """Process-wide `ResearchAgent` singleton, wired on top of the shared
    `ResearchOrchestrator` (Sprint 5) and `AIGovernancePlatform`
    (Sprint 15) — same `lru_cache` composition-root pattern as
    `tmis.legal_research.bootstrap.get_research_orchestrator` and
    `tmis.ai_governance.bootstrap.get_ai_governance_platform`.
    """
    return ResearchAgent(
        orchestrator=get_research_orchestrator(),
        governance=get_ai_governance_platform(),
    )
