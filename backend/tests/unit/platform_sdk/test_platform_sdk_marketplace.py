import pytest

from tmis.platform_sdk.extensions.engine import ExtensionEngine
from tmis.platform_sdk.extensions.store import InMemoryExtensionStore
from tmis.platform_sdk.marketplace.engine import MarketplaceEngine
from tmis.platform_sdk.marketplace.schemas import InvalidRatingError
from tmis.platform_sdk.marketplace.store import InMemoryReviewStore
from tmis.platform_sdk.permissions.engine import PermissionEngine
from tmis.platform_sdk.permissions.schemas import ExtensionPermission
from tmis.platform_sdk.permissions.store import InMemoryPermissionStore
from tmis.platform_sdk.plugin_registry.store import InMemoryPluginRegistry
from tmis.platform_sdk.plugin_system.schemas import PluginManifest, PluginType, PublishingStatus

FIRM = "firm-a"


def _published(plugin_id: str, plugin_type: PluginType = PluginType.AGENT) -> PluginManifest:
    manifest = PluginManifest(
        id=plugin_id,
        name=plugin_id.replace("-", " ").title(),
        version="1.0.0",
        plugin_type=plugin_type,
        author="a",
        description="une description avec un mot-clé fiscal",
        license="MIT",
        permissions=frozenset({"read_cases"}),
    )
    manifest.status = PublishingStatus.PUBLISHED
    return manifest


def _marketplace(registry: InMemoryPluginRegistry) -> tuple[MarketplaceEngine, ExtensionEngine]:
    permissions = PermissionEngine(InMemoryPermissionStore())
    extensions = ExtensionEngine(InMemoryExtensionStore(), registry, permissions)
    return MarketplaceEngine(registry, InMemoryReviewStore(), extensions), extensions


def test_search_only_returns_published_plugins() -> None:
    registry = InMemoryPluginRegistry()
    registry.register(_published("p1"))
    draft = _published("p2")
    draft.status = PublishingStatus.DEVELOPMENT
    registry.register(draft)
    marketplace, _ = _marketplace(registry)

    results = marketplace.search()

    assert [m.id for m in results] == ["p1"]


def test_search_filters_by_type_and_keyword() -> None:
    registry = InMemoryPluginRegistry()
    registry.register(_published("agent-1", PluginType.AGENT))
    registry.register(_published("connector-1", PluginType.CONNECTOR))
    marketplace, _ = _marketplace(registry)

    assert [m.id for m in marketplace.search(plugin_type=PluginType.CONNECTOR)] == ["connector-1"]
    assert [m.id for m in marketplace.search(query="fiscal")] == ["agent-1", "connector-1"]


def test_categories_reflect_published_types() -> None:
    registry = InMemoryPluginRegistry()
    registry.register(_published("agent-1", PluginType.AGENT))
    marketplace, _ = _marketplace(registry)

    assert marketplace.categories() == [PluginType.AGENT]


def test_average_rating_with_no_reviews_is_zero() -> None:
    registry = InMemoryPluginRegistry()
    registry.register(_published("p1"))
    marketplace, _ = _marketplace(registry)

    assert marketplace.average_rating("p1") == 0.0


def test_submit_review_and_average_rating() -> None:
    registry = InMemoryPluginRegistry()
    registry.register(_published("p1"))
    marketplace, _ = _marketplace(registry)

    marketplace.submit_review("p1", "firm-a", 4)
    marketplace.submit_review("p1", "firm-b", 2)

    assert marketplace.average_rating("p1") == 3.0
    assert len(marketplace.reviews_for("p1")) == 2


def test_review_rejects_out_of_range_rating() -> None:
    registry = InMemoryPluginRegistry()
    registry.register(_published("p1"))
    marketplace, _ = _marketplace(registry)

    with pytest.raises(InvalidRatingError):
        marketplace.submit_review("p1", FIRM, 6)


def test_install_uninstall_and_install_count() -> None:
    registry = InMemoryPluginRegistry()
    registry.register(_published("p1"))
    marketplace, _ = _marketplace(registry)

    marketplace.install(FIRM, "p1", frozenset({ExtensionPermission.READ_CASES}))
    assert marketplace.install_count("p1") == 1

    marketplace.uninstall(FIRM, "p1")
    assert marketplace.install_count("p1") == 0
