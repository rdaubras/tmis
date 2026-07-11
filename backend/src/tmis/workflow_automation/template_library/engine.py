from dataclasses import replace

from tmis.workflow_automation.action_engine.schemas import Action, new_action_id
from tmis.workflow_automation.template_library.schemas import WorkflowTemplate
from tmis.workflow_automation.trigger_engine.schemas import Trigger, new_trigger_id
from tmis.workflow_automation.workflow_engine.engine import WorkflowEngine
from tmis.workflow_automation.workflow_engine.schemas import Workflow, WorkflowStep


class TemplateLibrary:
    """The sprint's six example templates (ouverture de dossier,
    préparation d'audience, clôture de dossier, validation d'un
    brouillon, mise en demeure, revue contractuelle) plus whatever a
    cabinet registers of its own. Instantiating always goes through
    `WorkflowEngine.create`, so an instantiated workflow is a normal,
    versioned `Workflow` — never a second, parallel workflow
    representation."""

    def __init__(self, workflow_engine: WorkflowEngine) -> None:
        self._workflow_engine = workflow_engine
        self._templates: dict[str, WorkflowTemplate] = {}

    def register(self, template: WorkflowTemplate) -> None:
        self._templates[template.id] = template

    def get(self, template_id: str) -> WorkflowTemplate:
        template = self._templates.get(template_id)
        if template is None:
            raise KeyError(template_id)
        return template

    def list_templates(self, case_type: str | None = None) -> list[WorkflowTemplate]:
        templates = list(self._templates.values())
        if case_type is not None:
            templates = [t for t in templates if t.case_type == case_type]
        return templates

    def instantiate(
        self,
        template_id: str,
        firm_id: str,
        owner: str,
        overrides: dict[int, dict[str, str]] | None = None,
    ) -> Workflow:
        template = self.get(template_id)
        triggers = tuple(
            Trigger(id=new_trigger_id(), workflow_id="", trigger_type=spec.trigger_type,
                    config=dict(spec.config))
            for spec in template.trigger_specs
        )
        steps = []
        for spec in template.step_specs:
            config = dict(spec.action_config)
            if overrides and spec.order in overrides:
                config.update(overrides[spec.order])
            steps.append(
                WorkflowStep(
                    order=spec.order,
                    name=spec.name,
                    action=Action(
                        id=new_action_id(), workflow_id="", action_type=spec.action_type,
                        config=config,
                    ),
                    condition=spec.condition,
                    parallel_group=spec.parallel_group,
                )
            )

        workflow = self._workflow_engine.create(
            firm_id, template.name, owner,
            description=template.description,
            triggers=triggers,
            steps=tuple(steps),
        )
        # Triggers/actions were built before the workflow's real id was
        # known; backfill it now that `create()` has assigned one.
        workflow.triggers = tuple(replace(t, workflow_id=workflow.id) for t in workflow.triggers)
        workflow.steps = tuple(
            replace(s, action=replace(s.action, workflow_id=workflow.id))
            for s in workflow.steps
        )
        return workflow
