from functools import lru_cache

from tmis.ai_team.agents.catalog import default_descriptors
from tmis.ai_team.registry.store import InMemoryAgentRegistry


@lru_cache
def get_agent_registry() -> InMemoryAgentRegistry:
    """Process-wide `AgentRegistryPort` singleton, pre-populated with
    the default agent catalog (see docs/53-guide-creation-agent.md).
    Registering an additional agent at runtime (e.g. a marketplace
    agent) only requires calling `.register(...)` on this instance."""
    registry = InMemoryAgentRegistry()
    for descriptor in default_descriptors():
        registry.register(descriptor)
    return registry
