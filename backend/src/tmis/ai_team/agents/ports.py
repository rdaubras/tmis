from typing import Protocol

from tmis.ai.schemas.agent import AgentInput, AgentOutput
from tmis.ai_team.agents.schemas import AgentRole


class KernelPort(Protocol):
    """The narrow slice of `TMISKernel` an AI Team agent is allowed to
    call (see docs/53-guide-creation-agent.md). No agent may import
    `tmis.ai.kernel.TMISKernel` or a provider/connector directly — every
    agent depends on this port instead, satisfied in production by
    `tmis.ai_team.agents.kernel_adapter.KernelAgentAdapter`."""

    async def complete(self, prompt: str) -> str: ...


class TeamAgentPort(Protocol):
    """Every AI Team agent implements this — a specialization of
    `tmis.ai.schemas.agent.AgentPort` (Sprint 1) carrying a fixed
    `role` so the registry, team builder and delegation engine can
    match on it."""

    name: str
    role: AgentRole

    async def run(self, agent_input: AgentInput) -> AgentOutput: ...
