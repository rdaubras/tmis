# Guide — Workflows

## Les six statuts par défaut

`tmis.collaboration.workflow.schemas.WorkflowStatus` : `TODO`,
`IN_PROGRESS`, `IN_REVIEW`, `TO_VALIDATE`, `VALIDATED`, `ARCHIVED`.
`ConfigurableWorkflowEngine` autorise par défaut :

- la progression linéaire (`TODO` → ... → `VALIDATED`) ;
- un retour en arrière d'une étape (ex. `IN_REVIEW` → `IN_PROGRESS`) ;
- l'archivage depuis n'importe quel statut sauf `ARCHIVED` lui-même
  (terminal).

## Utiliser le workflow par défaut

```python
from tmis.collaboration.workflow.engine import ConfigurableWorkflowEngine
from tmis.collaboration.workflow.schemas import WorkflowStatus

engine = ConfigurableWorkflowEngine()
engine.can_transition(WorkflowStatus.TODO, WorkflowStatus.IN_PROGRESS)  # True
engine.transition(WorkflowStatus.TODO, WorkflowStatus.VALIDATED)  # ValueError
```

`transition()` lève `ValueError` pour tout changement non autorisé —
c'est ce que traduit l'API en `400 Bad Request`
(`POST /api/v1/collaboration/tasks/{id}/status`).

## Reconfigurer les transitions

```python
custom_transitions = {
    WorkflowStatus.TODO: {WorkflowStatus.VALIDATED},
    WorkflowStatus.VALIDATED: set(),
}
engine = ConfigurableWorkflowEngine(custom_transitions)
```

Un cabinet qui veut un circuit de validation plus court (ou plus
strict) fournit sa propre table sans toucher `tasks.TaskService`, qui
délègue systématiquement à `WorkflowEnginePort`.

## Tâches et workflow

`tasks.TaskService.update_status()` ne fait que déléguer à
`WorkflowEnginePort.transition()` — la même règle de transition
s'applique partout dans TMIS, pas seulement aux tâches. `depends_on`
n'est **pas** appliqué par le workflow : `TaskService.can_start()`
indique si les dépendances sont terminées (`VALIDATED`/`ARCHIVED`),
mais c'est un indicateur consultatif, pas un verrou — un workspace
peut toujours faire avancer une tâche urgente.

## Où brancher un moteur de workflow personnalisé

Toute classe implémentant `WorkflowEnginePort`
(`can_transition`, `transition`) peut remplacer
`ConfigurableWorkflowEngine` — injectée dans `TaskService` ou dans
`WorkspaceEngine` via `bootstrap.get_workspace_engine()`, sans changer
un seul appelant.
