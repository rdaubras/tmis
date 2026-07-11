import structlog

from tmis.platform_sdk.plugin_registry.ports import PluginRegistryPort
from tmis.platform_sdk.plugin_system.schemas import PluginManifest, PublishingStatus
from tmis.platform_sdk.publishing.ports import PublishingStorePort
from tmis.platform_sdk.publishing.schemas import (
    ALLOWED_TRANSITIONS,
    InvalidPublishingTransitionError,
    PublishingEvent,
    ValidationFailedError,
    new_publishing_event_id,
)
from tmis.platform_sdk.validation.engine import PluginValidator

_logger = structlog.get_logger(__name__)


class PublishingEngine:
    """The sprint's "PUBLICATION" lifecycle: Développement → Validation
    → Signature → Publication → Retrait, entirely historized — the
    same design as `tmis.cabinet_knowledge.governance` (Sprint 12),
    applied to plugin manifests instead of knowledge objects."""

    def __init__(
        self,
        store: PublishingStorePort,
        registry: PluginRegistryPort,
        validator: PluginValidator,
    ) -> None:
        self._store = store
        self._registry = registry
        self._validator = validator

    def validate_manifest(self, plugin_id: str, actor: str) -> PluginManifest:
        manifest = self._get(plugin_id)
        report = self._validator.validate(manifest)
        if not report.is_valid:
            raise ValidationFailedError(
                f"{plugin_id}: " + "; ".join(f"{i.field}: {i.message}" for i in report.issues)
            )
        return self._transition(manifest, PublishingStatus.VALIDATED, actor)

    def sign_manifest(self, plugin_id: str, actor: str) -> PluginManifest:
        manifest = self._get(plugin_id)
        manifest.signature = self._validator.sign(manifest)
        return self._transition(manifest, PublishingStatus.SIGNED, actor)

    def publish(self, plugin_id: str, actor: str) -> PluginManifest:
        manifest = self._get(plugin_id)
        return self._transition(manifest, PublishingStatus.PUBLISHED, actor)

    def retire(self, plugin_id: str, actor: str, reason: str | None = None) -> PluginManifest:
        manifest = self._get(plugin_id)
        return self._transition(manifest, PublishingStatus.RETIRED, actor, reason)

    def send_back_to_development(
        self, plugin_id: str, actor: str, reason: str | None = None
    ) -> PluginManifest:
        manifest = self._get(plugin_id)
        return self._transition(manifest, PublishingStatus.DEVELOPMENT, actor, reason)

    def history(self, plugin_id: str) -> list[PublishingEvent]:
        return self._store.history(plugin_id)

    def _get(self, plugin_id: str) -> PluginManifest:
        manifest = self._registry.get(plugin_id)
        if manifest is None:
            raise KeyError(plugin_id)
        return manifest

    def _transition(
        self,
        manifest: PluginManifest,
        to_status: PublishingStatus,
        actor: str,
        reason: str | None = None,
    ) -> PluginManifest:
        if to_status not in ALLOWED_TRANSITIONS[manifest.status]:
            raise InvalidPublishingTransitionError(manifest.status, to_status)
        from_status = manifest.status
        manifest.status = to_status
        self._registry.register(manifest)
        self._store.append(
            PublishingEvent(
                id=new_publishing_event_id(),
                plugin_id=manifest.id,
                from_status=from_status,
                to_status=to_status,
                actor=actor,
                reason=reason,
            )
        )
        _logger.info(
            "platform_sdk.publishing_transition",
            plugin_id=manifest.id,
            from_status=from_status.value,
            to_status=to_status.value,
            actor=actor,
        )
        return manifest
