from dataclasses import dataclass, field

from tmis.ai_team.agents.schemas import AgentRole


@dataclass(frozen=True, slots=True)
class AgentDescriptor:
    """A registry entry describing one agent — everything the Team
    Builder, Delegation Engine and marketplace need to know *about* an
    agent without running it (see docs/53-guide-creation-agent.md)."""

    id: str
    name: str
    role: AgentRole
    description: str
    skills: frozenset[str]
    tools: frozenset[str] = frozenset()
    compatible_models: frozenset[str] = frozenset({"openai", "anthropic"})
    estimated_cost_usd: float = 0.01
    average_duration_seconds: float = 5.0
    quality_score: float = 0.8
    version: str = "1.0.0"
    metadata: dict[str, str] = field(default_factory=dict)
