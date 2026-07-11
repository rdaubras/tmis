from tmis.ai_team.marketplace.schemas import MarketplaceListing
from tmis.cabinet_os.subscriptions.schemas import PlanTier

_PLAN_RANK: dict[PlanTier, int] = {
    PlanTier.SOLO: 0,
    PlanTier.CABINET: 1,
    PlanTier.ENTERPRISE: 2,
}


class InMemoryMarketplaceCatalog:
    """Implements `MarketplaceCatalogPort` (see
    docs/53-guide-creation-agent.md — Marketplace). `publish` may be
    called at any time — discovery is dynamic, mirroring
    `tmis.ai_team.registry.InMemoryAgentRegistry`."""

    def __init__(self) -> None:
        self._listings: dict[str, MarketplaceListing] = {}

    def publish(self, listing: MarketplaceListing) -> None:
        self._listings[listing.agent_id] = listing

    def get(self, agent_id: str) -> MarketplaceListing | None:
        return self._listings.get(agent_id)

    def list_all(self) -> list[MarketplaceListing]:
        return list(self._listings.values())

    def is_available_for_plan(self, agent_id: str, plan: PlanTier) -> bool:
        listing = self._listings.get(agent_id)
        if listing is None:
            return False
        if listing.subscription_plan_required is None:
            return True
        return _PLAN_RANK[plan] >= _PLAN_RANK[listing.subscription_plan_required]

    def missing_dependencies(self, agent_id: str) -> list[str]:
        listing = self._listings.get(agent_id)
        if listing is None:
            return []
        return [dep for dep in listing.dependencies if dep not in self._listings]
