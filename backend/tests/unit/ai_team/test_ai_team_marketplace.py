from tmis.ai_team.marketplace.schemas import MarketplaceListing
from tmis.ai_team.marketplace.store import InMemoryMarketplaceCatalog
from tmis.cabinet_os.subscriptions.schemas import PlanTier


def test_publish_is_dynamic() -> None:
    catalog = InMemoryMarketplaceCatalog()
    assert catalog.list_all() == []

    catalog.publish(MarketplaceListing(agent_id="agent-x", publisher="Acme", version="1.0.0"))

    assert len(catalog.list_all()) == 1
    assert catalog.get("agent-x") is not None


def test_listing_with_no_plan_requirement_is_available_to_everyone() -> None:
    catalog = InMemoryMarketplaceCatalog()
    catalog.publish(MarketplaceListing(agent_id="agent-x", publisher="Acme", version="1.0.0"))

    assert catalog.is_available_for_plan("agent-x", PlanTier.SOLO) is True


def test_listing_gated_by_plan_respects_tier_ordering() -> None:
    catalog = InMemoryMarketplaceCatalog()
    catalog.publish(
        MarketplaceListing(
            agent_id="agent-premium",
            publisher="Acme",
            version="1.0.0",
            subscription_plan_required=PlanTier.ENTERPRISE,
        )
    )

    assert catalog.is_available_for_plan("agent-premium", PlanTier.SOLO) is False
    assert catalog.is_available_for_plan("agent-premium", PlanTier.CABINET) is False
    assert catalog.is_available_for_plan("agent-premium", PlanTier.ENTERPRISE) is True


def test_unknown_agent_is_never_available() -> None:
    catalog = InMemoryMarketplaceCatalog()

    assert catalog.is_available_for_plan("does-not-exist", PlanTier.ENTERPRISE) is False


def test_missing_dependencies_are_reported() -> None:
    catalog = InMemoryMarketplaceCatalog()
    catalog.publish(
        MarketplaceListing(
            agent_id="agent-x",
            publisher="Acme",
            version="1.0.0",
            dependencies=("agent-y", "agent-z"),
        )
    )
    catalog.publish(MarketplaceListing(agent_id="agent-y", publisher="Acme", version="1.0.0"))

    assert catalog.missing_dependencies("agent-x") == ["agent-z"]


def test_no_missing_dependencies_when_all_are_published() -> None:
    catalog = InMemoryMarketplaceCatalog()
    catalog.publish(
        MarketplaceListing(
            agent_id="agent-x", publisher="Acme", version="1.0.0", dependencies=("agent-y",)
        )
    )
    catalog.publish(MarketplaceListing(agent_id="agent-y", publisher="Acme", version="1.0.0"))

    assert catalog.missing_dependencies("agent-x") == []
