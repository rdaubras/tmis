from tmis.platform_sdk.extensions.engine import ExtensionEngine
from tmis.platform_sdk.extensions.schemas import ExtensionInstance, ExtensionStatus
from tmis.platform_sdk.marketplace.ports import ReviewStorePort
from tmis.platform_sdk.marketplace.schemas import Review, new_review_id
from tmis.platform_sdk.permissions.schemas import ExtensionPermission
from tmis.platform_sdk.plugin_registry.ports import PluginRegistryPort
from tmis.platform_sdk.plugin_system.schemas import PluginManifest, PluginType, PublishingStatus


class MarketplaceEngine:
    """The sprint's "MARKETPLACE" foundations: catalogue, recherche,
    catégories, versions, avis, téléchargement, installation, mise à
    jour, désinstallation — install/update/uninstall are thin
    delegations to `tmis.platform_sdk.extensions.ExtensionEngine`,
    which owns the actual per-cabinet lifecycle; this module owns
    discovery (search/categories/reviews) on top of it. No UI is
    built this sprint, per the spec ("ne nécessite pas encore
    d'interface utilisateur complète")."""

    def __init__(
        self,
        registry: PluginRegistryPort,
        reviews: ReviewStorePort,
        extensions: ExtensionEngine,
    ) -> None:
        self._registry = registry
        self._reviews = reviews
        self._extensions = extensions

    def search(
        self, query: str | None = None, plugin_type: PluginType | None = None
    ) -> list[PluginManifest]:
        listings = [
            m for m in self._registry.list_all() if m.status is PublishingStatus.PUBLISHED
        ]
        if plugin_type is not None:
            listings = [m for m in listings if m.plugin_type is plugin_type]
        if query:
            needle = query.lower()
            listings = [
                m
                for m in listings
                if needle in m.name.lower() or needle in m.description.lower()
            ]
        return listings

    def categories(self) -> list[PluginType]:
        published = self.search()
        return sorted({m.plugin_type for m in published}, key=lambda t: t.value)

    def submit_review(self, plugin_id: str, firm_id: str, rating: int, comment: str = "") -> Review:
        review = Review(
            id=new_review_id(), plugin_id=plugin_id, firm_id=firm_id, rating=rating, comment=comment
        )
        self._reviews.save(review)
        return review

    def reviews_for(self, plugin_id: str) -> list[Review]:
        return self._reviews.list_for_plugin(plugin_id)

    def average_rating(self, plugin_id: str) -> float:
        reviews = self.reviews_for(plugin_id)
        if not reviews:
            return 0.0
        return sum(r.rating for r in reviews) / len(reviews)

    def install_count(self, plugin_id: str) -> int:
        return sum(
            1
            for instance in self._extensions.list_all()
            if instance.plugin_id == plugin_id
            and instance.status is not ExtensionStatus.UNINSTALLED
        )

    def install(
        self, firm_id: str, plugin_id: str, requested_permissions: frozenset[ExtensionPermission]
    ) -> ExtensionInstance:
        return self._extensions.install(firm_id, plugin_id, requested_permissions)

    def update(self, firm_id: str, plugin_id: str) -> ExtensionInstance:
        return self._extensions.update(firm_id, plugin_id)

    def uninstall(self, firm_id: str, plugin_id: str) -> ExtensionInstance:
        return self._extensions.uninstall(firm_id, plugin_id)
