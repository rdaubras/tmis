"""Demonstrates the Autonomous Legal Workflow Platform (ALWP) end to
end on several fictional workflows, showing rules, triggers,
sequential and parallel execution, retries, approval gating,
simulation, and rollback.

Run from `backend/`: `python -m scripts.demo_workflow_automation`

Uses a separate fictional firm (`firm-demo-alwp` / "Cabinet Démo
Lefèvre & Associés — Automatisation") so it never touches data from
other demo scripts. Every store is the in-memory reference
implementation, so this is safe to re-run freely.
"""

import asyncio

from tmis.ai_governance.human_validation.schemas import ValidationDecisionType
from tmis.workflow_automation.action_engine.schemas import (
    ACTION_CREATE_REMINDER,
    ACTION_CREATE_TASK,
    ACTION_GENERATE_DRAFT,
    ACTION_NOTIFY,
    Action,
    ActionResult,
)
from tmis.workflow_automation.bootstrap import (
    get_action_engine,
    get_approval_gateway_engine,
    get_execution_engine,
    get_rollback_engine,
    get_rule_engine,
    get_simulation_engine,
    get_template_library,
    get_workflow_audit_engine,
    get_workflow_engine,
)
from tmis.workflow_automation.condition_engine.schemas import Comparator, cond_compare
from tmis.workflow_automation.rollback.schemas import RollbackResult

FIRM_ID = "firm-demo-alwp"
FIRM_NAME = "Cabinet Démo Lefèvre & Associés — Automatisation"


def _print_section(title: str) -> None:
    print(f"\n--- {title} ---")


class _TaskHandler:
    action_type = ACTION_CREATE_TASK

    def execute(self, action: Action, context: dict[str, str]) -> ActionResult:
        return ActionResult(success=True, detail=f"Tâche créée : {action.config}")


class _ReminderHandler:
    action_type = ACTION_CREATE_REMINDER

    def execute(self, action: Action, context: dict[str, str]) -> ActionResult:
        return ActionResult(success=True, detail="Rappel programmé")


class _NotifyHandler:
    action_type = ACTION_NOTIFY

    def execute(self, action: Action, context: dict[str, str]) -> ActionResult:
        return ActionResult(success=True, detail="Notification envoyée")


class _DraftHandler:
    action_type = ACTION_GENERATE_DRAFT

    def execute(self, action: Action, context: dict[str, str]) -> ActionResult:
        return ActionResult(success=True, detail="Brouillon généré (jamais définitif)")


class _TaskRollbackHandler:
    action_type = ACTION_CREATE_TASK

    def compensate(self, action: Action, context: dict[str, str]) -> RollbackResult:
        return RollbackResult(compensated=True, detail="Tâche annulée")


def register_handlers() -> None:
    action_engine = get_action_engine()
    for handler in (_TaskHandler(), _ReminderHandler(), _NotifyHandler(), _DraftHandler()):
        action_engine.register(handler)
    get_rollback_engine().register(_TaskRollbackHandler())


async def run_workflow_ouverture_dossier() -> None:
    _print_section("Workflow 1 — Ouverture d'un dossier (exécution séquentielle)")

    library = get_template_library()
    template = next(t for t in library.list_templates() if t.case_type == "ouverture_dossier")
    workflow = library.instantiate(template.id, FIRM_ID, owner="avocat-1")
    get_workflow_engine().activate(FIRM_ID, workflow.id)
    print(
        f"Workflow instancié : « {workflow.name} » v{workflow.version}, "
        f"{len(workflow.steps)} étape(s)"
    )

    execution_engine = get_execution_engine()
    execution = await execution_engine.start(workflow, {"case_id": "dossier-ouverture-2026-05"})
    print(f"Statut : {execution.status.value}")
    for result in execution.step_results:
        detail = result.action_result.detail if result.action_result else "ignorée"
        print(f"  étape {result.step_order} : {detail}")

    get_workflow_audit_engine().record(
        FIRM_ID, workflow.id, "avocat-1", "workflow.executed", execution_id=execution.id
    )


async def run_workflow_preparation_audience() -> None:
    _print_section("Workflow 2 — Préparation d'une audience (règle + déclencheur)")

    rule_engine = get_rule_engine()
    rule = rule_engine.create_rule(
        FIRM_ID,
        "Audience dans moins de 7 jours",
        cond_compare("days_until_hearing", Comparator.LT, "7"),
        description="Déclenche la checklist de préparation d'audience.",
    )
    should_trigger = rule_engine.evaluate(FIRM_ID, rule.id, {"days_until_hearing": "3"})
    print(f"Règle « {rule.name} » évaluée sur J-3 : {should_trigger}")

    library = get_template_library()
    template = next(t for t in library.list_templates() if t.case_type == "preparation_audience")
    workflow = library.instantiate(template.id, FIRM_ID, owner="avocat-1")
    get_workflow_engine().activate(FIRM_ID, workflow.id)

    execution = await get_execution_engine().start(
        workflow, {"case_id": "dossier-audience-2026-06"}
    )
    print(f"Statut : {execution.status.value}, {len(execution.step_results)} étape(s) exécutée(s)")


async def run_workflow_mise_en_demeure_with_approval() -> None:
    _print_section("Workflow 3 — Mise en demeure (validation humaine obligatoire)")

    gateway = get_approval_gateway_engine()
    gateway.configure(FIRM_ID, ACTION_GENERATE_DRAFT, required=True)
    print(
        f"Validation requise pour '{ACTION_GENERATE_DRAFT}' : "
        f"{gateway.requires_approval(FIRM_ID, ACTION_GENERATE_DRAFT)}"
    )

    request = gateway.request_approval(
        FIRM_ID, "action-mise-en-demeure-1", "avocat-2", ("associe-1",)
    )
    print(f"Demande de validation créée — statut : {request.status.value}")
    gateway.decide(FIRM_ID, request.id, "associe-1", ValidationDecisionType.APPROVE)
    is_approved = gateway.is_approved(FIRM_ID, request.production_id)
    print(f"Après décision de l'associé : validée = {is_approved}")

    library = get_template_library()
    template = next(t for t in library.list_templates() if t.case_type == "mise_en_demeure")
    workflow = library.instantiate(template.id, FIRM_ID, owner="avocat-2")
    get_workflow_engine().activate(FIRM_ID, workflow.id)

    _print_section("Simulation avant exécution réelle")
    simulation = get_simulation_engine().simulate(workflow, {})
    print(f"Simulation : compléterait = {simulation.would_complete}")
    for step in simulation.steps:
        print(f"  {step.name} : exécuterait = {step.would_run}")

    execution = await get_execution_engine().start(workflow, {})
    print(f"Exécution réelle : {execution.status.value}")

    _print_section("Rollback de la tâche créée (démonstration)")
    rollback_engine = get_rollback_engine()
    if execution.step_results and execution.step_results[0].action_result:
        rollback_action = workflow.steps[0].action
        result = rollback_engine.rollback(FIRM_ID, execution.id, rollback_action, {})
        print(f"Rollback : compensée = {result.compensated} — {result.detail}")


async def main() -> None:
    print(f"=== Démonstration ALWP — {FIRM_NAME} ===")
    register_handlers()

    await run_workflow_ouverture_dossier()
    await run_workflow_preparation_audience()
    await run_workflow_mise_en_demeure_with_approval()

    _print_section("Synthèse — journal d'audit")
    for entry in get_workflow_audit_engine().list_for_firm(FIRM_ID):
        print(f"  [{entry.action}] workflow={entry.workflow_id} — {entry.detail}")

    print(
        "\nAucune automatisation n'a produit de décision juridique définitive ; "
        "chaque brouillon reste soumis à validation humaine."
    )


if __name__ == "__main__":
    asyncio.run(main())
