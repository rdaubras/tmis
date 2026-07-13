from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.legal_copilot_framework.copilot.marketplace import to_plugin_manifest
from tmis.legal_copilot_framework.copilot.schemas import CopilotStatus, LegalCopilot
from tmis.legal_copilot_framework.registry.schemas import CopilotManifest
from tmis.platform_sdk.plugin_system.schemas import PluginType


def test_to_plugin_manifest_maps_copilot_fields_onto_a_plugin_manifest() -> None:
    copilot = LegalCopilot(
        id="copilot-1",
        name="Copilote",
        domain=LegalDomain.CIVIL,
        description="desc",
        version="1.0.0",
        dependencies=("dep-1",),
        team_id="team-1",
        compatible_models=frozenset(),
        prompt_pack_id=None,
        knowledge_pack_ids=(),
        reasoning_pack_ids=(),
        document_pack_ids=(),
        workflow_pack_ids=(),
        validation_policy_ids=(),
        permissions=frozenset({"copilot.use"}),
    )
    manifest = CopilotManifest(
        copilot_id="copilot-1",
        version="1.0.0",
        domain=LegalDomain.CIVIL,
        author="author-1",
        status=CopilotStatus.DRAFT,
        compatibility="*",
    )

    plugin_manifest = to_plugin_manifest(copilot, manifest)

    assert plugin_manifest.id == "copilot-1"
    assert plugin_manifest.plugin_type is PluginType.COPILOT
    assert plugin_manifest.author == "author-1"
    assert plugin_manifest.dependencies == ("dep-1",)
    assert plugin_manifest.permissions == frozenset({"copilot.use"})
