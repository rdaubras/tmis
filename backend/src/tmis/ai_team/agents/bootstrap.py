from functools import lru_cache

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.ai_team.agents.catalog import build_default_agents
from tmis.ai_team.agents.kernel_adapter import KernelAgentAdapter
from tmis.ai_team.agents.ports import TeamAgentPort


@lru_cache
def get_default_agents() -> dict[str, TeamAgentPort]:
    """Process-wide default AI Team agent instances, keyed by agent id
    (see docs/53-guide-creation-agent.md). Built once against the
    shared `TMISKernel` singleton."""
    return build_default_agents(KernelAgentAdapter(get_kernel()))
