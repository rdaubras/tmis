from functools import lru_cache

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.ai_team.agents.kernel_adapter import KernelAgentAdapter
from tmis.core.config import get_settings
from tmis.platform.licensing.signing import LicenseKeySigner
from tmis.platform_sdk.developer_portal.engine import DeveloperPortalService
from tmis.platform_sdk.events_sdk.bus import PlatformEventBus
from tmis.platform_sdk.examples.registration import register_example_plugins
from tmis.platform_sdk.extensions.engine import ExtensionEngine
from tmis.platform_sdk.extensions.store import InMemoryExtensionStore
from tmis.platform_sdk.marketplace.engine import MarketplaceEngine
from tmis.platform_sdk.marketplace.store import InMemoryReviewStore
from tmis.platform_sdk.permissions.engine import PermissionEngine
from tmis.platform_sdk.permissions.store import InMemoryPermissionStore
from tmis.platform_sdk.plugin_loader.engine import PluginLoader
from tmis.platform_sdk.plugin_loader.store import InMemoryPluginImplementationRegistry
from tmis.platform_sdk.plugin_registry.store import InMemoryPluginRegistry
from tmis.platform_sdk.publishing.engine import PublishingEngine
from tmis.platform_sdk.publishing.store import InMemoryPublishingStore
from tmis.platform_sdk.sandbox.engine import SandboxExecutor
from tmis.platform_sdk.validation.engine import PluginValidator


@lru_cache
def get_plugin_registry() -> InMemoryPluginRegistry:
    """Process-wide composition root for `tmis.platform_sdk` (see
    docs/65-architecture-platform-sdk.md). Seeded once with the five
    example plugins so the Marketplace and CLI have something real to
    browse/validate/publish/install out of the box."""
    registry = InMemoryPluginRegistry()
    register_example_plugins(registry, get_plugin_implementation_registry())
    return registry


@lru_cache
def get_plugin_implementation_registry() -> InMemoryPluginImplementationRegistry:
    return InMemoryPluginImplementationRegistry()


@lru_cache
def get_permission_store() -> InMemoryPermissionStore:
    return InMemoryPermissionStore()


@lru_cache
def get_permission_engine() -> PermissionEngine:
    return PermissionEngine(get_permission_store())


@lru_cache
def get_plugin_signer() -> LicenseKeySigner:
    return LicenseKeySigner(get_settings().plugin_signing_key)


@lru_cache
def get_plugin_validator() -> PluginValidator:
    return PluginValidator(get_plugin_registry(), get_plugin_signer())


@lru_cache
def get_publishing_store() -> InMemoryPublishingStore:
    return InMemoryPublishingStore()


@lru_cache
def get_publishing_engine() -> PublishingEngine:
    return PublishingEngine(get_publishing_store(), get_plugin_registry(), get_plugin_validator())


@lru_cache
def get_plugin_loader() -> PluginLoader:
    return PluginLoader(get_plugin_registry(), get_plugin_implementation_registry())


@lru_cache
def get_platform_event_bus() -> PlatformEventBus:
    return PlatformEventBus()


@lru_cache
def get_sandbox_executor() -> SandboxExecutor:
    return SandboxExecutor(
        get_plugin_loader(),
        get_permission_engine(),
        get_platform_event_bus(),
        kernel=KernelAgentAdapter(get_kernel()),
    )


@lru_cache
def get_extension_store() -> InMemoryExtensionStore:
    return InMemoryExtensionStore()


@lru_cache
def get_extension_engine() -> ExtensionEngine:
    return ExtensionEngine(get_extension_store(), get_plugin_registry(), get_permission_engine())


@lru_cache
def get_review_store() -> InMemoryReviewStore:
    return InMemoryReviewStore()


@lru_cache
def get_marketplace_engine() -> MarketplaceEngine:
    return MarketplaceEngine(get_plugin_registry(), get_review_store(), get_extension_engine())


@lru_cache
def get_developer_portal_service() -> DeveloperPortalService:
    return DeveloperPortalService()
