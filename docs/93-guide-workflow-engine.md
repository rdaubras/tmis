# Guide — Workflow Engine & Execution Engine

## Créer et versionner un workflow

```python
from tmis.workflow_automation.bootstrap import get_workflow_engine
from tmis.workflow_automation.workflow_engine.schemas import WorkflowStep
from tmis.workflow_automation.action_engine.schemas import Action, new_action_id, ACTION_CREATE_TASK

engine = get_workflow_engine()
workflow = engine.create(
    "firm-123", "Ouverture d'un dossier", owner="avocat-1",
    steps=(
        WorkflowStep(0, "Créer la tâche d'accueil",
                     Action(new_action_id(), "", ACTION_CREATE_TASK)),
    ),
)
engine.activate("firm-123", workflow.id)
```

Chaque `Workflow` est une **version immuable** : `new_version()` crée
un nouveau snapshot qui hérite des champs non fournis, et
`activate()` archive automatiquement la version précédemment active
pour la même `workflow_key` — il n'y a jamais deux versions actives en
même temps.

```python
v2 = engine.new_version("firm-123", workflow.workflow_key, owner="avocat-1", description="v2")
engine.activate("firm-123", v2.id)   # v1 passe automatiquement à ARCHIVED
```

## Exécuter un workflow

```python
from tmis.workflow_automation.bootstrap import get_execution_engine

execution_engine = get_execution_engine()
execution = await execution_engine.start(workflow, context={"case_id": "dossier-1"})
print(execution.status, execution.step_results)
```

Les étapes s'exécutent **séquentiellement**, sauf celles partageant le
même `parallel_group` (non nul), exécutées concurremment via
`asyncio.gather`. Chaque étape passe par `retry.WorkflowRetryPolicy`
(backoff exponentiel) et un timeout configurable avant d'être
considérée en échec.

## Reprise après interruption

Une étape qui échoue après épuisement des tentatives interrompt
l'exécution **sans faire avancer** `current_step_index` — l'étape
fautive reste la prochaine à rejouer.

```python
if execution.status.value == "failed":
    execution = await execution_engine.resume(execution, workflow, context)
```

## Modèles de workflow

`template_library.TemplateLibrary` fournit six modèles par défaut
(ouverture de dossier, préparation d'audience, clôture de dossier,
validation d'un brouillon, mise en demeure, revue contractuelle),
tous personnalisables via `overrides` :

```python
from tmis.workflow_automation.bootstrap import get_template_library

library = get_template_library()
workflow = library.instantiate(
    template_id, "firm-123", owner="avocat-1",
    overrides={0: {"priority": "high"}},
)
```

`instantiate()` passe toujours par `WorkflowEngine.create()` — un
workflow issu d'un modèle est un `Workflow` normal, versionné comme
n'importe quel autre.
