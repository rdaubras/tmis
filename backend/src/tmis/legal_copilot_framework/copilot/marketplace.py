from tmis.legal_copilot_framework.copilot.schemas import LegalCopilot
from tmis.legal_copilot_framework.registry.schemas import CopilotManifest
from tmis.platform_sdk.plugin_system.schemas import PluginManifest, PluginType

_LICENSE = "proprietary"
"""No `LegalCopilot.license` field exists yet (out of this sprint's
scope) — every copilot published to the marketplace is proprietary to
the cabinet that authored it until a licensing model is designed."""


def to_plugin_manifest(copilot: LegalCopilot, manifest: CopilotManifest) -> PluginManifest:
    """Bridges a `LegalCopilot` into `platform_sdk.plugin_system`'s
    `PluginManifest` so it can flow through the existing publishing
    (`platform_sdk.publishing`) and marketplace (`platform_sdk.
    marketplace`) machinery unchanged — "préparer un futur Marketplace
    de copilotes" (Sprint 24 Phase 12) without a second catalogue.
    `PluginType.COPILOT` was added to the enum for exactly this."""
    return PluginManifest(
        id=copilot.id,
        name=copilot.name,
        version=copilot.version,
        plugin_type=PluginType.COPILOT,
        author=manifest.author,
        description=copilot.description,
        license=_LICENSE,
        permissions=copilot.permissions,
        dependencies=copilot.dependencies,
        compatibility=manifest.compatibility,
    )
