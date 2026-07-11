from tmis.ai_team.agents.schemas import AgentRole
from tmis.ai_team.registry.schemas import AgentDescriptor


class InMemoryAgentRegistry:
    """Implements `AgentRegistryPort` (see docs/53-guide-creation-agent.md).
    `register` may be called at any time — the registry has no fixed
    membership, so a marketplace agent installed later registers the
    same way the default catalog does at bootstrap."""

    def __init__(self) -> None:
        self._descriptors: dict[str, AgentDescriptor] = {}

    def register(self, descriptor: AgentDescriptor) -> None:
        self._descriptors[descriptor.id] = descriptor

    def get(self, agent_id: str) -> AgentDescriptor | None:
        return self._descriptors.get(agent_id)

    def list_all(self) -> list[AgentDescriptor]:
        return list(self._descriptors.values())

    def list_by_role(self, role: AgentRole) -> list[AgentDescriptor]:
        return [d for d in self._descriptors.values() if d.role == role]

    def list_by_skill(self, skill: str) -> list[AgentDescriptor]:
        return [d for d in self._descriptors.values() if skill in d.skills]
