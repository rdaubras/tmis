from typing import Protocol

from tmis.ai_team.agents.schemas import AgentRole
from tmis.ai_team.registry.schemas import AgentDescriptor


class AgentRegistryPort(Protocol):
    """Port implemented by every interchangeable agent registry (see
    docs/53-guide-creation-agent.md). Supports dynamic registration:
    `register` is callable at any time, not only at bootstrap, so a
    new agent (including a future marketplace agent) can be added
    without a code change to the registry itself."""

    def register(self, descriptor: AgentDescriptor) -> None: ...

    def get(self, agent_id: str) -> AgentDescriptor | None: ...

    def list_all(self) -> list[AgentDescriptor]: ...

    def list_by_role(self, role: AgentRole) -> list[AgentDescriptor]: ...

    def list_by_skill(self, skill: str) -> list[AgentDescriptor]: ...
