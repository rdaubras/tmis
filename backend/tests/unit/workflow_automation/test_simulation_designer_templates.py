from tmis.workflow_automation.action_engine import ACTION_CREATE_TASK, Action, new_action_id
from tmis.workflow_automation.condition_engine import ConditionEngine
from tmis.workflow_automation.condition_engine.schemas import Comparator, cond_compare
from tmis.workflow_automation.simulation import SimulationEngine
from tmis.workflow_automation.template_library import TemplateLibrary, build_default_templates
from tmis.workflow_automation.trigger_engine.schemas import Trigger, TriggerType, new_trigger_id
from tmis.workflow_automation.workflow_designer import DesignerNodeKind, workflow_to_graph
from tmis.workflow_automation.workflow_engine import (
    InMemoryWorkflowStore,
    WorkflowEngine,
    WorkflowStep,
)


def test_simulation_never_calls_action_engine_and_reports_step_outcomes() -> None:
    we = WorkflowEngine(InMemoryWorkflowStore())
    gated = WorkflowStep(
        0,
        "gated",
        Action(new_action_id(), "wf", ACTION_CREATE_TASK),
        condition=cond_compare("go", Comparator.EQ, "yes"),
    )
    ungated = WorkflowStep(1, "ungated", Action(new_action_id(), "wf", ACTION_CREATE_TASK))
    workflow = we.create("firm-1", "Test", owner="a", steps=(gated, ungated))
    engine = SimulationEngine(ConditionEngine())

    report = engine.simulate(workflow, {"go": "no"})

    assert report.would_complete is True
    assert report.steps[0].would_run is False
    assert report.steps[0].skip_reason
    assert report.steps[1].would_run is True


def test_simulation_workflow_level_condition_failure_stops_early() -> None:
    we = WorkflowEngine(InMemoryWorkflowStore())
    workflow = we.create(
        "firm-1", "Test", owner="a", conditions=(cond_compare("ready", Comparator.EQ, "true"),)
    )
    engine = SimulationEngine(ConditionEngine())

    report = engine.simulate(workflow, {"ready": "false"})

    assert report.would_complete is False
    assert report.workflow_condition_failure
    assert report.steps == ()


def test_workflow_to_graph_produces_trigger_and_action_nodes() -> None:
    we = WorkflowEngine(InMemoryWorkflowStore())
    trigger = Trigger(
        id=new_trigger_id(), workflow_id="", trigger_type=TriggerType.DOCUMENT_CREATED
    )
    step = WorkflowStep(0, "step-1", Action(new_action_id(), "wf", ACTION_CREATE_TASK))
    workflow = we.create("firm-1", "Test", owner="a", triggers=(trigger,), steps=(step,))

    graph = workflow_to_graph(workflow)

    kinds = {n.kind for n in graph.nodes}
    assert DesignerNodeKind.TRIGGER in kinds
    assert DesignerNodeKind.ACTION in kinds
    assert len(graph.edges) >= 1


def test_template_library_lists_and_filters_by_case_type() -> None:
    we = WorkflowEngine(InMemoryWorkflowStore())
    library = TemplateLibrary(we)
    for template in build_default_templates():
        library.register(template)

    assert len(library.list_templates()) == 6
    assert len(library.list_templates(case_type="cloture_dossier")) == 1


def test_template_library_instantiate_creates_a_real_versioned_workflow() -> None:
    we = WorkflowEngine(InMemoryWorkflowStore())
    library = TemplateLibrary(we)
    templates = build_default_templates()
    for template in templates:
        library.register(template)
    contract_template = next(t for t in templates if t.case_type == "revue_contractuelle")

    workflow = library.instantiate(contract_template.id, "firm-1", owner="avocat-1")

    assert workflow.version == 1
    assert len(workflow.steps) == 2
    assert all(s.action.workflow_id == workflow.id for s in workflow.steps)
    assert all(t.workflow_id == workflow.id for t in workflow.triggers)


def test_template_library_instantiate_applies_overrides() -> None:
    we = WorkflowEngine(InMemoryWorkflowStore())
    library = TemplateLibrary(we)
    templates = build_default_templates()
    for template in templates:
        library.register(template)
    opening_template = next(t for t in templates if t.case_type == "ouverture_dossier")

    workflow = library.instantiate(
        opening_template.id, "firm-1", owner="avocat-1", overrides={0: {"priority": "high"}}
    )

    assert workflow.steps[0].action.config.get("priority") == "high"
