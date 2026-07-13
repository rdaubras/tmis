import pytest

from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.legal_copilot_framework.copilot.schemas import CopilotStatus
from tmis.legal_copilot_framework.registry.engine import CopilotRegistry
from tmis.legal_copilot_framework.registry.schemas import CopilotManifest
from tmis.legal_copilot_framework.registry.store import InMemoryCopilotRegistryStore


def _manifest(copilot_id: str = "copilot-1", version: str = "1.0.0") -> CopilotManifest:
    return CopilotManifest(
        copilot_id=copilot_id,
        version=version,
        domain=LegalDomain.CIVIL,
        author="author",
        status=CopilotStatus.DRAFT,
    )


def _registry() -> CopilotRegistry:
    return CopilotRegistry(InMemoryCopilotRegistryStore())


def test_register_and_get_latest() -> None:
    registry = _registry()
    registry.register(_manifest(version="1.0.0"))
    registry.register(_manifest(version="1.1.0"))

    latest = registry.get_latest("copilot-1")

    assert latest.version == "1.1.0"


def test_get_unknown_copilot_raises_key_error() -> None:
    registry = _registry()
    with pytest.raises(KeyError):
        registry.get("missing")


def test_get_specific_version() -> None:
    registry = _registry()
    registry.register(_manifest(version="1.0.0"))
    registry.register(_manifest(version="1.1.0"))

    assert registry.get("copilot-1", version="1.0.0").version == "1.0.0"


def test_get_unknown_version_raises_key_error() -> None:
    registry = _registry()
    registry.register(_manifest(version="1.0.0"))

    with pytest.raises(KeyError):
        registry.get("copilot-1", version="9.9.9")


def test_history_never_drops_earlier_versions() -> None:
    registry = _registry()
    registry.register(_manifest(version="1.0.0"))
    registry.register(_manifest(version="1.1.0"))

    assert [m.version for m in registry.history("copilot-1")] == ["1.0.0", "1.1.0"]


def test_list_all_returns_latest_manifest_per_copilot() -> None:
    registry = _registry()
    registry.register(_manifest("copilot-1", "1.0.0"))
    registry.register(_manifest("copilot-1", "1.1.0"))
    registry.register(_manifest("copilot-2", "1.0.0"))

    versions = {m.copilot_id: m.version for m in registry.list_all()}

    assert versions == {"copilot-1": "1.1.0", "copilot-2": "1.0.0"}


def test_set_status_updates_the_stored_manifest() -> None:
    registry = _registry()
    registry.register(_manifest(version="1.0.0"))

    updated = registry.set_status("copilot-1", "1.0.0", CopilotStatus.PUBLISHED)

    assert updated.status is CopilotStatus.PUBLISHED
    assert registry.get("copilot-1", version="1.0.0").status is CopilotStatus.PUBLISHED
