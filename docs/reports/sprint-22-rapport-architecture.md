# Rapport d'architecture — Sprint 22 (Cloud Operations, extensions)

## Résumé

Le Sprint 22 étend `backend/src/tmis/cloud_operations/` avec 9
nouveaux sous-modules (`audit_pipeline`, `cost_monitoring`,
`ai_monitoring`, `workflow_monitoring`, `integration_monitoring`,
`tenant_monitoring`, `security_monitoring`, `retention`, `exports`)
et 14 nouveaux endpoints REST. Ce sprint fait suite à un prompt
utilisateur initialement rédigé comme une « Enterprise Observability
& Reliability Platform » distincte (`tmis.observability/`) ; l'analyse
préalable a montré un recouvrement massif (~12-13 modules) avec le
Sprint 21 tout juste livré. Après consultation explicite de
l'utilisateur via `AskUserQuestion` (« Treat as Sprint 22, extend
cloud_operations » — option choisie), la portée a été réduite aux 9
domaines authentiquement nouveaux ; aucun module du Sprint 21 n'a été
reconstruit.

Points de contact hors `cloud_operations/` :

- `tmis/cloud_operations/bootstrap.py` — 9 nouveaux getters
  `@lru_cache`, composant des moteurs de `ai_fabric`,
  `ai_governance`, `business_platform`, `identity_platform`,
  `integration_hub`, `platform.cost_control`, `workflow_automation`.
- `tmis/cloud_operations/api/routes.py` — 14 nouveaux endpoints.
- `tmis/integration_hub/synchronization/engine.py` —
  `SynchronizationEngine.run_pull` accepte désormais un paramètre
  optionnel `monitoring: ConnectorMonitoringEngine | None`, chronomètre
  l'opération et l'enregistre dans les deux branches (succès/échec).
- `tmis/integration_hub/bootstrap.py` —
  `get_synchronization_engine()` branche `get_connector_monitoring_
  engine()` en production.
- `tmis/workflow_automation/execution_engine/engine.py` —
  `_run_from` enregistre désormais une `WorkflowRunMetrics` par
  exécution via un nouveau helper `_record_workflow_metrics`.

## Conformité aux principes architecturaux

- **Clean Architecture / DDD** : chaque nouveau module suit
  `schemas.py` → `ports.py` (si un point d'extension local est
  nécessaire) → `store.py` (uniquement quand l'état est propre au
  module) → `engine.py` → `__init__.py`. Cinq des neuf modules
  (`cost_monitoring`, `workflow_monitoring`, `integration_monitoring`,
  `tenant_monitoring`, `security_monitoring`) sont purement
  compositionnels et n'ont pas de `store.py`.
- **Composer, ne jamais reconstruire** : table complète dans
  docs/126-architecture-cloud-operations-sprint22.md — huit
  compositions explicites vers des moteurs des Sprints 9, 10, 14, 15,
  17, 18, 19, 20, 21. La chaîne d'export (`exports.
  ObservabilityExportEngine` → `business_platform.exports.
  ExportEngine.export_table` → `cabinet_os.reports.exporters.
  CsvReportExporter`) est la troisième couche de réutilisation d'une
  même logique CSV/JSON, sans aucune duplication.
- **Reader port** (nouveau patron introduit ce sprint) :
  `workflow_monitoring`/`integration_monitoring` typent leur
  dépendance contre un `Protocol` de lecture local
  (`WorkflowMetricsReaderPort`/`ConnectorMetricsReaderPort`) plutôt
  que d'élargir le port d'écriture partagé des Sprints 17/18 ou de
  recourir à un `# type: ignore` — voir docs/126, section dédiée.
- **Isolation multi-tenant** : chaque schéma porte un `firm_id`
  explicite quand la donnée est scopée par cabinet
  (`AuditPipelineEvent`, `CostMonitoringSnapshot`,
  `TenantMonitoringSnapshot`, `AIQualityIncident.firm_id | None`) ;
  `security_monitoring` est délibérément plateforme entière, jamais
  scopé par erreur.
- **Documenter les écarts plutôt que les approximer** :
  `WorkflowRunMetrics.validation_count`/`retry_count`/
  `ai_automations_triggered` sont rapportés à `0` par la nouvelle
  instrumentation, faute de suivi à cette granularité dans
  `ExecutionEngine` aujourd'hui — documenté dans le code et dans
  docs/128 et docs/131 plutôt que silencieusement approximé.

## Rapport d'instrumentation — sinks livrés sans appelant, maintenant branchés

| Sink | Sprint d'origine | État avant ce sprint | État après ce sprint |
|---|---|---|---|
| `workflow_automation.metrics.WorkflowMetricsEngine` | 17 | Aucun appelant confirmé par recherche directe dans tout le code | `ExecutionEngine._run_from` enregistre une `WorkflowRunMetrics` par exécution (bloc `finally`) |
| `integration_hub.monitoring.ConnectorMonitoringEngine` | 18 | Aucun appelant confirmé par recherche directe dans tout le code | `SynchronizationEngine.run_pull` enregistre chronométrage + succès/échec (paramètre optionnel, rétrocompatible) |

Ce constat est distinct des 3 points « représentatifs »
d'instrumentation déjà ajoutés au Sprint 21 (middleware API,
`ExecutionEngine.start`, `RouterEngine.route`), qui alimentaient
`cloud_operations.metrics`/`.tracing` — ici, ce sont deux capacités
antérieures, complètes mais jamais connectées, qui sont corrigées à
leur source.

## Décision structurante : bug réel trouvé en testant l'API directement

`GET /cloud-operations/tenants/{firm_id}` pour un cabinet sans
abonnement `business_platform.subscriptions` provoquait une
`KeyError` non gérée, remontant en `500` au lieu d'un `404` propre —
découvert en exécutant directement l'endpoint avant de finaliser le
test d'intégration, plutôt qu'en devinant le code de statut attendu.
Corrigé par un `try/except KeyError` explicite dans le handler de
route, retournant `HTTPException(404, "firm has no subscription")`.
Ce n'est pas un défaut hérité d'un sprint antérieur : il a été
introduit et corrigé au sein de ce même sprint.

## Dette technique identifiée

Voir la table complète dans
docs/131-guide-migration-cloud-operations-sprint22.md : compteurs de
workflow non suivis à grain fin (`validation_count`/`retry_count`/
`ai_automations_triggered`), `collaboration.audit`/`platform.audit`
non inclus dans `audit_pipeline` (scopés espace de travail plutôt que
cabinet), `retention.RetentionEngine` qui expose la politique sans
exécuter de purge, instrumentation `integration_monitoring`/
`workflow_monitoring` limitée à un seul point d'entrée chacun
(`run_pull`, `_run_from`).

## Vérification finale

```
$ .venv/bin/ruff check src/ tests/
All checks passed!

$ .venv/bin/mypy src/
Success: no issues found in 1686 source files

$ .venv/bin/pytest -q
1754 passed, 4 skipped, 2 warnings in 10.82s
```

1754 tests passent (1727 hérités des Sprints 1-21, 27 nouveaux dédiés
au Sprint 22 : 19 unitaires couvrant les 9 nouveaux sous-modules par
grappes fonctionnelles, 10 d'intégration couvrant les 14 nouveaux
endpoints REST — dont le cas 404 du bug corrigé ci-dessus).
