# Guide — Supervision workflow et intégrations (Sprint 22)

## Deux sinks livrés au Sprint 17/18, jamais branchés

`workflow_automation.metrics.WorkflowMetricsEngine` (Sprint 17) et
`integration_hub.monitoring.ConnectorMonitoringEngine` (Sprint 18)
existaient déjà dans le code, avec leur `store.py` et leur
`engine.py` complets, mais une recherche directe dans l'ensemble du
code applicatif a confirmé qu'aucun appelant n'existait pour
`.record()` sur l'un ou l'autre avant ce sprint — une capacité
livrée mais jamais connectée. Ce sprint corrige ce point mort à deux
niveaux : instrumentation réelle des points de production (voir
docs/131-guide-migration-cloud-operations-sprint22.md) et exposition
en lecture via deux nouveaux moteurs de `cloud_operations`.

## Supervision workflow

`workflow_monitoring.WorkflowMonitoringEngine.snapshot()` agrège
`sink.all()` (toutes les `WorkflowRunMetrics` historisées) :
nombre total d'exécutions, durée moyenne, total d'erreurs, de
tentatives, de validations, d'annulations.

```python
GET /cloud-operations/workflow-monitoring
```

**Limite documentée** : `validation_count`, `retry_count` et
`ai_automations_triggered` sont actuellement toujours rapportés à
`0`. `workflow_automation.execution_engine.ExecutionEngine` ne suit
pas ces compteurs à cette granularité aujourd'hui — plutôt que de les
approximer silencieusement, ce sprint les documente comme un écart
réel entre ce que le schéma promet et ce que l'instrumentation
actuelle peut fournir.

## Supervision intégrations

`integration_monitoring.IntegrationMonitoringEngine` lit
`ConnectorMetricsReaderPort` (voir docs/126, section « reader
port ») pour deux vues :

- `.snapshot(connector_id)` — opérations totales, taux de réussite,
  durée moyenne pour un connecteur donné.
- `.overview()` — la même vue pour chaque `connector_id` distinct
  observé dans l'historique (`{m.connector_id for m in sink.all()}`).

```python
GET /cloud-operations/integration-monitoring
```

## Port de lecture local

Les deux moteurs typent leur dépendance contre un `Protocol` défini
localement dans leur propre `ports.py`
(`WorkflowMetricsReaderPort`/`ConnectorMetricsReaderPort`), plutôt
que contre le port d'écriture partagé du Sprint 17/18 — voir
docs/126-architecture-cloud-operations-sprint22.md pour la
justification complète de ce choix.
