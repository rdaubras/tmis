from tmis.business_platform.marketplace_subscriptions.engine import MarketplaceSubscriptionEngine
from tmis.legal_copilot_framework.copilot.marketplace import to_plugin_manifest
from tmis.legal_copilot_framework.copilot.ports import CopilotStorePort
from tmis.legal_copilot_framework.copilot.schemas import CopilotActivation, LegalCopilot
from tmis.legal_copilot_framework.registry.engine import CopilotRegistry
from tmis.platform_sdk.extensions.engine import ExtensionEngine
from tmis.platform_sdk.extensions.schemas import ExtensionInstance, ExtensionStatus
from tmis.platform_sdk.permissions.schemas import ExtensionPermission
from tmis.platform_sdk.plugin_registry.ports import PluginRegistryPort
from tmis.platform_sdk.plugin_system.schemas import PublishingStatus
from tmis.platform_sdk.publishing.engine import PublishingEngine


def _to_activation(instance: ExtensionInstance) -> CopilotActivation:
    return CopilotActivation(
        firm_id=instance.firm_id,
        copilot_id=instance.plugin_id,
        active=instance.status is ExtensionStatus.ACTIVE,
        version=instance.version,
        granted_permissions=frozenset(p.value for p in instance.granted_permissions),
        updated_at=instance.updated_at,
    )


class CopilotEngine:
    """Owns the assembled `LegalCopilot` catalog. Definition (`define`)
    is normally called by `sdk.CopilotBuilder`, never directly with
    hand-built pack ids — this engine trusts the ids it is given were
    already validated.

    Per-firm activation is no longer a second store to keep in sync:
    `activate`/`deactivate` write only through `platform_sdk.
    extensions.ExtensionEngine`, via `business_platform.
    marketplace_subscriptions.MarketplaceSubscriptionEngine` (which
    already wraps it for licensing/billing without introducing a
    second install path — see docs/171-audit-marketplace.md).
    `CopilotActivation` is recomputed from the resulting
    `ExtensionInstance` on every read."""

    def __init__(
        self,
        store: CopilotStorePort,
        registry: CopilotRegistry,
        plugin_registry: PluginRegistryPort,
        publishing: PublishingEngine,
        extensions: ExtensionEngine,
        subscriptions: MarketplaceSubscriptionEngine,
    ) -> None:
        self._store = store
        self._registry = registry
        self._plugin_registry = plugin_registry
        self._publishing = publishing
        self._extensions = extensions
        self._subscriptions = subscriptions

    def define(self, copilot: LegalCopilot) -> LegalCopilot:
        self._store.save(copilot)
        return copilot

    def get(self, copilot_id: str) -> LegalCopilot:
        copilot = self._store.get(copilot_id)
        if copilot is None:
            raise KeyError(copilot_id)
        return copilot

    def list_all(self) -> list[LegalCopilot]:
        return self._store.list_all()

    def activate(self, firm_id: str, copilot_id: str, actor: str) -> CopilotActivation:
        """Installs the copilot for `firm_id` through the marketplace
        subscription mechanism, publishing it first (`platform_sdk.
        publishing.PublishingEngine`) if this is its first activation
        anywhere — a copilot has no separate pricing model of its own
        yet (out of this sprint's scope), so every activation is a
        zero-price subscription; this still gives it a real
        `ExtensionSubscription`/license grant for a future sprint to
        price without changing this call site."""
        copilot = self.get(copilot_id)
        self._ensure_published(copilot, actor)
        requested_permissions = frozenset(ExtensionPermission(p) for p in copilot.permissions)
        self._subscriptions.subscribe(
            firm_id, copilot_id, requested_permissions=requested_permissions
        )
        return self._require_activation(firm_id, copilot_id)

    def deactivate(self, firm_id: str, copilot_id: str) -> CopilotActivation:
        self._subscriptions.unsubscribe(firm_id, copilot_id)
        return self._require_activation(firm_id, copilot_id)

    def is_active(self, firm_id: str, copilot_id: str) -> bool:
        instance = self._find_instance(firm_id, copilot_id)
        return instance is not None and instance.status is ExtensionStatus.ACTIVE

    def active_copilots(self, firm_id: str) -> list[LegalCopilot]:
        return [
            self.get(instance.plugin_id)
            for instance in self._extensions.list_for_firm(firm_id)
            if instance.status is ExtensionStatus.ACTIVE
        ]

    def _ensure_published(self, copilot: LegalCopilot, actor: str) -> None:
        manifest = self._plugin_registry.get(copilot.id)
        if manifest is None:
            copilot_manifest = self._registry.get_latest(copilot.id)
            manifest = to_plugin_manifest(copilot, copilot_manifest)
            self._plugin_registry.register(manifest)
        if manifest.status is PublishingStatus.DEVELOPMENT:
            manifest = self._publishing.validate_manifest(copilot.id, actor)
        if manifest.status is PublishingStatus.VALIDATED:
            manifest = self._publishing.sign_manifest(copilot.id, actor)
        if manifest.status is PublishingStatus.SIGNED:
            self._publishing.publish(copilot.id, actor)

    def _find_instance(self, firm_id: str, copilot_id: str) -> ExtensionInstance | None:
        for instance in self._extensions.list_for_firm(firm_id):
            if instance.plugin_id == copilot_id:
                return instance
        return None

    def _require_activation(self, firm_id: str, copilot_id: str) -> CopilotActivation:
        instance = self._find_instance(firm_id, copilot_id)
        if instance is None:
            raise KeyError((firm_id, copilot_id))
        return _to_activation(instance)
