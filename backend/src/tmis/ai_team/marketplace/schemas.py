from dataclasses import dataclass, field

from tmis.cabinet_os.subscriptions.schemas import PlanTier


@dataclass(frozen=True, slots=True)
class MarketplaceListing:
    """A publishable, discoverable agent entry (see
    docs/53-guide-creation-agent.md — Marketplace). Separate from
    `tmis.ai_team.registry.AgentDescriptor`: the registry is what the
    Coordinator resolves roles against *right now*; a listing is what
    a future marketplace UI would show *before* an agent is installed
    into the registry. No UI is built this sprint — only this data
    model and the catalog operations it needs (discovery, versioning,
    dependencies, subscription-gated activation)."""

    agent_id: str
    publisher: str
    version: str
    description: str = ""
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    subscription_plan_required: PlanTier | None = None
