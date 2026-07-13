import pytest

from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.legal_copilot_framework.workflow_packs.engine import WorkflowPackEngine
from tmis.legal_copilot_framework.workflow_packs.store import InMemoryWorkflowPackStore
from tmis.workflow_automation.template_library.defaults import build_default_templates
from tmis.workflow_automation.template_library.engine import TemplateLibrary
from tmis.workflow_automation.workflow_engine.engine import WorkflowEngine
from tmis.workflow_automation.workflow_engine.store import InMemoryWorkflowStore

FIRM = "firm-a"


def _engine() -> tuple[WorkflowPackEngine, TemplateLibrary]:
    library = TemplateLibrary(WorkflowEngine(InMemoryWorkflowStore()))
    for template in build_default_templates():
        library.register(template)
    return WorkflowPackEngine(InMemoryWorkflowPackStore(), library), library


def test_register_pack_versions_increment() -> None:
    engine, _ = _engine()
    first = engine.register_pack("wp-1", "Pack", LegalDomain.CIVIL)
    second = engine.register_pack("wp-1", "Pack", LegalDomain.CIVIL)

    assert first.version == 1
    assert second.version == 2


def test_get_unknown_pack_raises_key_error() -> None:
    engine, _ = _engine()
    with pytest.raises(KeyError):
        engine.get("missing")


def test_instantiate_pack_creates_one_workflow_per_template() -> None:
    engine, library = _engine()
    template = library.list_templates(case_type="revue_contractuelle")[0]
    engine.register_pack(
        "wp-1", "Pack", LegalDomain.COMMERCIAL, workflow_template_ids=(template.id,)
    )

    workflows = engine.instantiate_pack(FIRM, "owner-1", "wp-1")

    assert len(workflows) == 1
    assert workflows[0].firm_id == FIRM
