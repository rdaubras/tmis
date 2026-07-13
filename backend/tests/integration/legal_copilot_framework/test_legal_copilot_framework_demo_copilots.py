"""End-to-end integration test for the sprint's five MVP demo copilots
(Phase 12): builds each through the real bootstrap composition root and
checks every copilot demonstrates its agents, packs, workflows, document
models, and validation policy, per the sprint's own scope note ("ne pas
chercher à implémenter toute la logique métier")."""

from tmis.legal_copilot_framework.bootstrap import (
    get_copilot_engine,
    get_copilot_registry,
    get_document_pack_engine,
    get_knowledge_pack_engine,
    get_reasoning_pack_engine,
    get_workflow_pack_engine,
    seed_demo_copilots_once,
)
from tmis.legal_copilot_framework.copilot.schemas import CopilotStatus

_EXPECTED_COPILOT_IDS = {
    "copilot-contentieux",
    "copilot-droit-societes",
    "copilot-droit-fiscal",
    "copilot-droit-social",
    "copilot-contrats",
}
_DEMO_FIRM_ID = "demo-firm"


def test_seeding_produces_the_five_expected_copilots() -> None:
    copilot_ids = set(seed_demo_copilots_once())

    assert copilot_ids == _EXPECTED_COPILOT_IDS


def test_every_demo_copilot_has_agents_and_a_registered_manifest() -> None:
    seed_demo_copilots_once()
    copilot_engine = get_copilot_engine()
    registry = get_copilot_registry()

    for copilot_id in _EXPECTED_COPILOT_IDS:
        copilot = copilot_engine.get(copilot_id)
        assert copilot.team_id
        assert copilot.status is CopilotStatus.DRAFT

        manifest = registry.get_latest(copilot_id)
        assert manifest.author == "tmis-legal-copilot-framework"
        assert manifest.status is CopilotStatus.DRAFT


def test_every_demo_copilot_declares_every_pack_type() -> None:
    seed_demo_copilots_once()
    copilot_engine = get_copilot_engine()

    for copilot_id in _EXPECTED_COPILOT_IDS:
        copilot = copilot_engine.get(copilot_id)
        assert copilot.prompt_pack_id is not None
        assert len(copilot.knowledge_pack_ids) == 1
        assert len(copilot.reasoning_pack_ids) == 1
        assert len(copilot.document_pack_ids) == 1
        assert len(copilot.workflow_pack_ids) == 1
        assert len(copilot.validation_policy_ids) == 1


def test_every_demo_copilots_document_pack_resolves_to_real_templates() -> None:
    seed_demo_copilots_once()
    copilot_engine = get_copilot_engine()
    document_packs = get_document_pack_engine()

    for copilot_id in _EXPECTED_COPILOT_IDS:
        copilot = copilot_engine.get(copilot_id)
        pack_id = copilot.document_pack_ids[0]
        templates = document_packs.resolve_document_templates(pack_id)
        assert len(templates) >= 1


def test_every_demo_copilots_knowledge_pack_resolves_for_the_demo_firm() -> None:
    seed_demo_copilots_once()
    copilot_engine = get_copilot_engine()
    knowledge_packs = get_knowledge_pack_engine()

    for copilot_id in _EXPECTED_COPILOT_IDS:
        copilot = copilot_engine.get(copilot_id)
        pack_id = copilot.knowledge_pack_ids[0]
        objects = knowledge_packs.resolve_objects(_DEMO_FIRM_ID, pack_id)
        assert len(objects) == 1


def test_every_demo_copilots_reasoning_pack_resolves_a_pattern() -> None:
    seed_demo_copilots_once()
    copilot_engine = get_copilot_engine()
    reasoning_packs = get_reasoning_pack_engine()

    for copilot_id in _EXPECTED_COPILOT_IDS:
        copilot = copilot_engine.get(copilot_id)
        pack_id = copilot.reasoning_pack_ids[0]
        patterns = reasoning_packs.resolve_patterns(_DEMO_FIRM_ID, pack_id)
        assert len(patterns) == 1


def test_every_demo_copilots_workflow_pack_can_be_instantiated() -> None:
    seed_demo_copilots_once()
    copilot_engine = get_copilot_engine()
    workflow_packs = get_workflow_pack_engine()

    for copilot_id in _EXPECTED_COPILOT_IDS:
        copilot = copilot_engine.get(copilot_id)
        pack_id = copilot.workflow_pack_ids[0]
        workflows = workflow_packs.instantiate_pack(_DEMO_FIRM_ID, "demo-owner", pack_id)
        assert len(workflows) == 1
        assert workflows[0].firm_id == _DEMO_FIRM_ID


def test_activating_a_demo_copilot_for_a_firm_makes_it_active() -> None:
    seed_demo_copilots_once()
    copilot_engine = get_copilot_engine()
    firm_id = "firm-demo-activation"

    assert copilot_engine.active_copilots(firm_id) == []

    copilot_engine.activate(firm_id, "copilot-contentieux")

    active_ids = {c.id for c in copilot_engine.active_copilots(firm_id)}
    assert active_ids == {"copilot-contentieux"}
