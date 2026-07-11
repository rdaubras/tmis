from typing import Protocol

from tmis.ai_team.marketplace.schemas import MarketplaceListing
from tmis.cabinet_os.subscriptions.schemas import PlanTier


class MarketplaceCatalogPort(Protocol):
    """Port implemented by every interchangeable marketplace catalog
    (see docs/53-guide-creation-agent.md — Marketplace)."""

    def publish(self, listing: MarketplaceListing) -> None: ...

    def get(self, agent_id: str) -> MarketplaceListing | None: ...

    def list_all(self) -> list[MarketplaceListing]: ...

    def is_available_for_plan(self, agent_id: str, plan: PlanTier) -> bool: ...

    def missing_dependencies(self, agent_id: str) -> list[str]: ...
