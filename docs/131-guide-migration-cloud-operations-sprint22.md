# Guide — Instrumentation réelle ajoutée au Sprint 22

## Contexte

Les Sprints 17 et 18 avaient livré `workflow_automation.metrics.
WorkflowMetricsEngine` et `integration_hub.monitoring.
ConnectorMonitoringEngine` avec leurs schémas, ports, stores et
moteurs complets — mais une recherche directe dans tout le code
applicatif, effectuée avant d'écrire la moindre ligne de ce sprint, a
confirmé qu'aucun appelant réel n'existait pour `.record()` sur l'un
ou l'autre. C'est une capacité livrée mais jamais branchée à une
source de données réelle — distincte des 3 points d'instrumentation
« représentatifs » déjà ajoutés au Sprint 21 (middleware API,
`ExecutionEngine.start`/`_run_from` pour la télémétrie/traçage,
`RouterEngine.route`), qui touchaient des sinks différents
(`cloud_operations.metrics`/`.tracing`).

Ce sprint corrige ce point mort à sa source, pas seulement en lecture
côté `cloud_operations`.

## `integration_hub.synchronization.SynchronizationEngine`

`run_pull` accepte désormais un paramètre optionnel
`monitoring: ConnectorMonitoringEngine | None = None`. Le corps
original de la méthode est conservé intact sous `_run_pull` ; la
méthode publique l'enveloppe d'un chronométrage
(`time.perf_counter()`) et d'un `try/except Exception`, appelant dans
les deux branches un helper `_record_operation(job, record_count, *,
success, started, error=None)` qui délègue à
`monitoring.record(job.connector_id, job.firm_id, "pull",
success=..., duration_ms=..., record_count=..., error=...)`
uniquement si `monitoring is not None` — rétrocompatible, aucun site
d'appel existant n'est cassé (le paramètre est optionnel et son
comportement par défaut est inchangé).

`integration_hub.bootstrap.get_synchronization_engine()` passe
désormais `get_connector_monitoring_engine()` en troisième argument,
branchant l'instrumentation en production sans qu'aucun appelant du
moteur n'ait à changer.

## `workflow_automation.execution_engine.ExecutionEngine`

`_run_from` appelle désormais `self._record_workflow_metrics
(execution)` dans son bloc `finally`, après `self._close_span
(execution)`. Le nouveau helper construit un `WorkflowRunMetrics`
(durée calculée depuis `started_at`/`completed_at`, nombre d'étapes,
erreur si `ExecutionStatus.FAILED`, annulation si
`ExecutionStatus.CANCELLED`) et l'enregistre via
`workflow_automation.bootstrap.get_workflow_metrics_engine().record
(...)`.

**Écart documenté, pas approximé** : `validation_count`,
`retry_count` et `ai_automations_triggered` sont actuellement toujours
`0`, faute de suivi à cette granularité dans `ExecutionEngine`
aujourd'hui. Ce choix — rapporter `0` plutôt qu'inventer une valeur
plausible — est délibéré : une métrique fausse est pire qu'une
métrique manquante documentée.

## Dette technique identifiée par ce sprint

| Sujet | État | Action future suggérée |
|---|---|---|
| `validation_count`/`retry_count`/`ai_automations_triggered` | Toujours `0`, non suivi à la bonne granularité | Instrumenter `ValidationGate`/`RetryPolicy`/`ActionEngine` individuellement dans un futur sprint |
| `collaboration.audit`/`platform.audit` | Non inclus dans `audit_pipeline` (scopés espace de travail, pas `firm_id`) | Adaptateur espace de travail → cabinet, si le besoin business se confirme |
| `retention.RetentionEngine` | Expose la politique et le calcul d'expiration, n'exécute aucune purge | Job de purge périodique dans un futur sprint infrastructure |
| `IntegrationMonitoringEngine`/`WorkflowMonitoringEngine` | Un seul point d'instrumentation réel chacun (`run_pull`, `_run_from`) | Étendre aux autres méthodes (`run_push`, retries, etc.) au fil de l'eau |

Ce tableau suit le même principe que la dette technique documentée
au Sprint 21 : rien n'est caché, chaque limite connue est nommée
explicitement plutôt que découverte plus tard en production.
