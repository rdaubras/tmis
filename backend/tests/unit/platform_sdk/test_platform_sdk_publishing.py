import pytest

from tmis.platform.licensing.signing import LicenseKeySigner
from tmis.platform_sdk.plugin_registry.store import InMemoryPluginRegistry
from tmis.platform_sdk.plugin_system.schemas import PluginManifest, PluginType, PublishingStatus
from tmis.platform_sdk.publishing.engine import PublishingEngine
from tmis.platform_sdk.publishing.schemas import (
    InvalidPublishingTransitionError,
    ValidationFailedError,
)
from tmis.platform_sdk.publishing.store import InMemoryPublishingStore
from tmis.platform_sdk.validation.engine import PluginValidator


def _manifest(**overrides: object) -> PluginManifest:
    defaults: dict[str, object] = {
        "id": "p1",
        "name": "Plugin 1",
        "version": "1.0.0",
        "plugin_type": PluginType.AGENT,
        "author": "a",
        "description": "...",
        "license": "MIT",
    }
    defaults.update(overrides)
    return PluginManifest(**defaults)  # type: ignore[arg-type]


def _engine(registry: InMemoryPluginRegistry | None = None) -> PublishingEngine:
    registry = registry or InMemoryPluginRegistry()
    validator = PluginValidator(registry, LicenseKeySigner("test-secret"))
    return PublishingEngine(InMemoryPublishingStore(), registry, validator)


def test_full_lifecycle_reaches_published() -> None:
    registry = InMemoryPluginRegistry()
    registry.register(_manifest())
    engine = _engine(registry)

    engine.validate_manifest("p1", actor="dev1")
    engine.sign_manifest("p1", actor="dev1")
    manifest = engine.publish("p1", actor="dev1")

    assert manifest.status is PublishingStatus.PUBLISHED
    assert manifest.signature is not None


def test_validate_fails_for_invalid_manifest() -> None:
    registry = InMemoryPluginRegistry()
    registry.register(_manifest(license=""))
    engine = _engine(registry)

    with pytest.raises(ValidationFailedError):
        engine.validate_manifest("p1", actor="dev1")

    assert registry.get("p1").status is PublishingStatus.DEVELOPMENT  # type: ignore[union-attr]


def test_cannot_sign_before_validation() -> None:
    registry = InMemoryPluginRegistry()
    registry.register(_manifest())
    engine = _engine(registry)

    with pytest.raises(InvalidPublishingTransitionError):
        engine.sign_manifest("p1", actor="dev1")


def test_retire_only_allowed_from_published() -> None:
    registry = InMemoryPluginRegistry()
    registry.register(_manifest())
    engine = _engine(registry)

    with pytest.raises(InvalidPublishingTransitionError):
        engine.retire("p1", actor="dev1")


def test_retired_is_terminal() -> None:
    registry = InMemoryPluginRegistry()
    registry.register(_manifest())
    engine = _engine(registry)
    engine.validate_manifest("p1", actor="dev1")
    engine.sign_manifest("p1", actor="dev1")
    engine.publish("p1", actor="dev1")

    engine.retire("p1", actor="dev1", reason="obsolete")

    with pytest.raises(InvalidPublishingTransitionError):
        engine.publish("p1", actor="dev1")


def test_history_records_every_transition_in_order() -> None:
    registry = InMemoryPluginRegistry()
    registry.register(_manifest())
    engine = _engine(registry)
    engine.validate_manifest("p1", actor="dev1")
    engine.sign_manifest("p1", actor="dev1")
    engine.publish("p1", actor="dev1")

    history = engine.history("p1")

    assert [e.to_status.value for e in history] == ["validated", "signed", "published"]
    assert all(e.actor == "dev1" for e in history)


def test_send_back_to_development_from_validated() -> None:
    registry = InMemoryPluginRegistry()
    registry.register(_manifest())
    engine = _engine(registry)
    engine.validate_manifest("p1", actor="dev1")

    manifest = engine.send_back_to_development("p1", actor="reviewer1", reason="needs rework")

    assert manifest.status is PublishingStatus.DEVELOPMENT
