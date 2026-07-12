# Rapport d'architecture — Sprint 17 (Autonomous Legal Workflow Platform)

## Résumé

Le Sprint 17 ajoute `backend/src/tmis/workflow_automation/` (17
sous-modules + une couche API) au-dessus du socle existant. Aucun
module métier des Sprints 2-16 n'a été modifié ; seul
`tmis/api/v1/router.py` a été touché hors `workflow_automation/`,
pour brancher le nouveau routeur REST.

## Conformité aux principes architecturaux

- **Clean Architecture / DDD / SOLID / Event Driven Architecture** :
  chaque sous-module suit le patron `schemas.py` → `ports.py` (si
  persistance dédiée) → implémentation(s) → composition dans
  `workflow_automation/bootstrap.py` ; `event_bus.WorkflowEventBus`
  fournit le socle événementiel, standalone comme
  `CollaborationEventBus`/`GovernanceEventBus`.
- **Le système ne remplace jamais l'avocat** : vérifié
  structurellement — `action_engine` ne connaît que des types
  d'actions administratives/documentaires/organisationnelles
  (`create_task`, `notify`, `launch_ai_analysis`, `generate_draft`,
  `enrich_knowledge`, `create_reminder`, `call_integration`), aucune
  action de "décision juridique" n'existe dans le vocabulaire du
  moteur.
- **Toutes les automatisations sont configurables, explicables et
  auditables** : `rule_engine`/`condition_engine` permettent de
  configurer des règles sans toucher au code ; `action_engine` et
  `rollback` journalisent systématiquement, même en cas d'échec ;
  `audit.WorkflowAuditEngine` fournit un journal append-only dédié
  avec export CSV.
- **Toutes les interactions IA passent par l'AI Intelligence
  Fabric** : aucun sous-module de ce sprint n'appelle un modèle brut —
  `action_engine.ACTION_LAUNCH_AI_ANALYSIS` est un type d'action
  extensible dont l'implémentation réelle (Sprint futur) devra passer
  par `tmis.ai_fabric.fabric.AIIntelligenceFabric`.

## Décision structurante : quatre "Workflow" au sens différent

`workflow_automation.workflow_engine.Workflow` (définition de
processus métier automatisé : déclencheurs/conditions/étapes/actions,
versionnée) est le quatrième concept nommé "Workflow" de TMIS, après
`case_intelligence.workflow.CaseIntelligenceWorkflow` (Sprint 4),
`collaboration.workflow.ConfigurableWorkflowEngine` (cycle Kanban
d'une tâche, Sprint 8), et un troisième homonyme évité par nommage
distinct partout ailleurs. Documenté explicitement plutôt que
renommé, sur le principe déjà acté pour les collisions
`GovernanceEngine`/`PolicyEngine`.

## Décision structurante : reprise après interruption

`execution_engine.ExecutionEngine._run_from()` n'incrémente
`WorkflowExecution.current_step_index` qu'après le succès complet
d'une étape (ou d'un groupe parallèle). Une étape qui échoue après
épuisement de `retry.WorkflowRetryPolicy` lève une exception qui
interrompt l'exécution **avant** cet incrément — `resume()` reprend
donc exactement à l'étape fautive. Vérifié par
`test_execution_engine_resume_continues_from_failed_step`.

## Décision structurante : simulation sans effet réel

`simulation.SimulationEngine` n'importe **aucune** dépendance vers
`action_engine` — architecturalement, il ne peut jamais déclencher une
action réelle. Il n'évalue que les conditions (workflow et étapes)
contre un contexte fictif et retourne des prédictions
(`would_run`/`skip_reason`), jamais un effet de bord.

## Réutilisation explicite des sprints précédents

- `ai_governance.human_validation.HumanValidationEngine` (Sprint 15) —
  enveloppé directement par `approval_gateway`, cinquième réutilisation
  du patron d'approbation après `cabinet_knowledge.validation`,
  `collaboration.approvals`, `ai_governance.human_validation` lui-même
  et `strategic_intelligence.review` (Sprint 16).
- `collaboration.notifications.NotificationEngine` (Sprint 8) —
  enveloppé directement par `notifications`.
- `cabinet_knowledge.playbooks`/`cabinet_knowledge.governance` (Sprint
  12) — patron catalogue-vs-instance et
  `ALLOWED_TRANSITIONS`/append-only repris pour
  `template_library`/`workflow_engine`.
- `ai_fabric.retry.RetryPolicy` (Sprint 14) — patron de backoff
  exponentiel, réimplémenté localement (bounded context distinct)
  pour `retry.WorkflowRetryPolicy`.
- `ai_governance.audit.AIAuditEngine`/`ai_governance.evaluation.
  GovernanceEvaluator` (Sprint 15) — patrons repris pour
  `audit.WorkflowAuditEngine` et `metrics.WorkflowMetricsEngine`
  (sink-fanout).

## Vérification de non-régression

`ruff check src tests` et `mypy src` : aucune erreur sur 1249 fichiers
source (contre 1170 avant ce sprint). `pytest` : **1478 tests passés,
4 ignorés** (contre 1418 avant ce sprint) — 60 tests dédiés à
`workflow_automation` (55 unitaires + 5 d'intégration), couverture
globale du dépôt 95,70 %, sans qu'aucun des 1418 tests précédents
n'ait été modifié.

## Voir aussi

- docs/92-architecture-workflow-automation.md pour les diagrammes
  Mermaid détaillés.
- docs/reports/sprint-17-demo-workflows.md pour la démonstration
  complète sur trois workflows fictifs.
