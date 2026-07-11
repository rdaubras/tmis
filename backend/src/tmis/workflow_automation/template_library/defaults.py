"""The sprint's six example templates: ouverture d'un dossier,
préparation d'une audience, clôture d'un dossier, validation d'un
brouillon, gestion d'une mise en demeure, revue contractuelle."""

from tmis.workflow_automation.action_engine.schemas import (
    ACTION_CREATE_REMINDER,
    ACTION_CREATE_TASK,
    ACTION_ENRICH_KNOWLEDGE,
    ACTION_GENERATE_DRAFT,
    ACTION_LAUNCH_AI_ANALYSIS,
    ACTION_NOTIFY,
)
from tmis.workflow_automation.template_library.schemas import (
    TemplateStepSpec,
    TemplateTriggerSpec,
    WorkflowTemplate,
    new_template_id,
)
from tmis.workflow_automation.trigger_engine.schemas import TriggerType


def build_default_templates() -> list[WorkflowTemplate]:
    return [
        WorkflowTemplate(
            id=new_template_id(),
            name="Ouverture d'un dossier",
            case_type="ouverture_dossier",
            description="Crée les tâches et notifications d'ouverture d'un nouveau dossier.",
            trigger_specs=(TemplateTriggerSpec(TriggerType.CASE_UPDATED, {"field": "status"}),),
            step_specs=(
                TemplateStepSpec(0, "Créer la tâche d'accueil", ACTION_CREATE_TASK),
                TemplateStepSpec(1, "Notifier l'équipe", ACTION_NOTIFY),
            ),
        ),
        WorkflowTemplate(
            id=new_template_id(),
            name="Préparation d'une audience",
            case_type="preparation_audience",
            description="Génère la checklist de préparation dès la création d'une audience.",
            trigger_specs=(
                TemplateTriggerSpec(
                    TriggerType.BUSINESS_EVENT,
                    {"source": "cabinet_os.hearings", "label": "hearing_created"},
                ),
            ),
            step_specs=(
                TemplateStepSpec(0, "Créer la checklist", ACTION_CREATE_TASK),
                TemplateStepSpec(1, "Créer un rappel J-3", ACTION_CREATE_REMINDER),
                TemplateStepSpec(2, "Notifier l'avocat responsable", ACTION_NOTIFY),
            ),
        ),
        WorkflowTemplate(
            id=new_template_id(),
            name="Clôture d'un dossier",
            case_type="cloture_dossier",
            description="Vérifications et notifications de clôture d'un dossier.",
            trigger_specs=(TemplateTriggerSpec(TriggerType.CASE_UPDATED, {"field": "status"}),),
            step_specs=(
                TemplateStepSpec(0, "Créer la tâche de vérification finale", ACTION_CREATE_TASK),
                TemplateStepSpec(1, "Notifier le client", ACTION_NOTIFY),
            ),
        ),
        WorkflowTemplate(
            id=new_template_id(),
            name="Validation d'un brouillon",
            case_type="validation_brouillon",
            description="Prépare le circuit de signature après validation d'un brouillon.",
            trigger_specs=(TemplateTriggerSpec(TriggerType.VALIDATION, {"target_type": "draft"}),),
            step_specs=(
                TemplateStepSpec(0, "Préparer le circuit de signature", ACTION_CREATE_TASK),
                TemplateStepSpec(1, "Notifier les signataires", ACTION_NOTIFY),
            ),
        ),
        WorkflowTemplate(
            id=new_template_id(),
            name="Gestion d'une mise en demeure",
            case_type="mise_en_demeure",
            description="Génère et notifie une mise en demeure à partir d'un modèle.",
            trigger_specs=(
                TemplateTriggerSpec(
                    TriggerType.BUSINESS_EVENT,
                    {"source": "case_intelligence", "label": "deadline_missed"},
                ),
            ),
            step_specs=(
                TemplateStepSpec(
                    0, "Générer le brouillon de mise en demeure", ACTION_GENERATE_DRAFT
                ),
                TemplateStepSpec(1, "Notifier l'avocat responsable", ACTION_NOTIFY),
            ),
        ),
        WorkflowTemplate(
            id=new_template_id(),
            name="Revue contractuelle",
            case_type="revue_contractuelle",
            description="Lance l'analyse IA d'un contrat importé puis enrichit le Knowledge "
            "Engine.",
            trigger_specs=(
                TemplateTriggerSpec(TriggerType.DOCUMENT_CREATED, {"document_type": "contrat"}),
            ),
            step_specs=(
                TemplateStepSpec(0, "Lancer l'analyse IA du contrat", ACTION_LAUNCH_AI_ANALYSIS),
                TemplateStepSpec(1, "Enrichir le Knowledge Engine", ACTION_ENRICH_KNOWLEDGE),
            ),
        ),
    ]
