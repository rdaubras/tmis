# Démo — Sprint 22 (Cloud Operations, extensions)

Démonstration exécutée via `TestClient(app)` contre l'API réelle
(`/api/v1/business-platform`, `/cloud-operations`) et les singletons
`cloud_operations.bootstrap` — sortie capturée telle quelle, sur un
cabinet fictif `demo-firm-sprint22`.

## 1. Un cabinet démo souscrit un essai

```
subscription trial: 200 trial
```

`POST /api/v1/business-platform/subscriptions/trial` (Sprint 20)
crée une souscription `PROFESSIONAL` en statut `trial` — suffisant
pour que `business_platform.analytics.AnalyticsEngine` calcule un
MRR, sans avoir besoin d'`activate`.

## 2. Un incident est ouvert pour ce cabinet

```
incident: 200 inc-470bee7b570d open
```

`POST /cloud-operations/incidents` (Sprint 21).

## 3. Snapshot tenant — chaîne complète business_platform → cloud_operations

```
status: 200
MRR: 199.0 | open incidents: 1 | modules actifs: 13
```

`GET /cloud-operations/tenants/{firm_id}` compose en un seul appel
`business_platform.analytics.AnalyticsEngine` (MRR),
`business_platform.usage.UsageEngine` (quotas, non affiché ici) et
`cloud_operations.incident_management.IncidentManagementEngine`
(l'incident ouvert à l'étape 2) — la « chaîne complète de
traçabilité » demandée par le sprint, du module métier jusqu'à la
supervision opérationnelle.

## 3bis. Le bug corrigé ce sprint : 404 propre, pas de 500

```
status: 404 detail: firm has no subscription
```

Un cabinet sans abonnement provoquait une `500` non gérée avant la
correction appliquée dans ce sprint (voir docs/129 et le rapport
d'architecture) — désormais un `404` explicite.

## 4. Scan qualité IA — détection et historisation

```
status: 200
 - hallucination : Cette clause est manifestement illégale, sans aucune source
incidents historisés au total: 1
```

`POST /cloud-operations/ai-quality/{firm_id}/scan` exécute
`ai_governance.hallucination_detection.HallucinationDetectionEngine`
(Sprint 15) et historise le résultat — auparavant strictement
éphémère, jamais conservé au-delà d'un seul appel.

## 5. Timeline d'audit fusionnée

```
status: 200 | événements: 0
```

`GET /cloud-operations/audit/{firm_id}` fusionne
`identity_platform.audit`, `ai_governance.audit`,
`workflow_automation.audit` pour ce cabinet — `0` ici car ce scénario
de démo ne déclenche aucun événement de génération IA gouvernée ni de
workflow pour `demo-firm-sprint22` (le scan de l'étape 4 alimente
`ai_monitoring`, pas `ai_governance.audit`, qui trace les
générations, pas les scans qualité).

## 6. Supervision workflow et intégrations — sinks Sprint 17/18 désormais alimentés

```
workflow-monitoring: {'total_runs': 0, 'average_duration_ms': 0.0, 'total_errors': 0,
                       'total_retries': 0, 'total_validations': 0, 'total_cancellations': 0}
integration-monitoring (overview): []
```

Ces deux endpoints lisent des sinks confirmés sans appelant avant ce
sprint (voir docs/131). Les valeurs sont à zéro ici car ce processus
de démonstration ne fait tourner ni workflow ni synchronisation de
connecteur — même principe de transparence que la démo du Sprint 21,
qui rapportait honnêtement `workflows_executed: 0` plutôt que de
simuler une valeur non observée. L'instrumentation réelle
(`ExecutionEngine._run_from`, `SynchronizationEngine.run_pull`) est
vérifiée par les tests dédiés
(`tests/unit/cloud_operations/test_workflow_integration_monitoring.py`),
qui font tourner un vrai `ExecutionEngine`/`SynchronizationEngine` et
observent des valeurs non nulles.

## 7. Supervision sécurité plateforme

```
security-monitoring: {'total_events': 0, 'events_by_type': {}}
```

`GET /cloud-operations/security-monitoring` lit
`identity_platform.security_events.SecurityEventBus` — vide ici car
aucune connexion/déconnexion n'a eu lieu dans ce scénario de démo ;
`tests/unit/cloud_operations/test_tenant_security_monitoring.py::
test_security_monitoring_counts_events_by_type_across_the_bus`
démontre le comptage réel sur un bus peuplé.

## 8. Politique de rétention — lecture puis modification

```
avant: {'category': 'audit_events', 'retention_days': 2555}
après: {'category': 'audit_events', 'retention_days': 3650}
```

`GET`/`POST /cloud-operations/retention/audit_events` — la valeur par
défaut (2 555 jours ≈ 7 ans) est portée à 3 650 jours (10 ans) pour
ce cabinet démo, démontrant la modification en place.

## 9. Export CSV des incidents du cabinet démo

```
status: 200 | filename: incidents.csv
id,title,severity,status,firm_id,opened_at
```

`GET /cloud-operations/exports/incidents?export_format=csv` —
délégué à `business_platform.exports.ExportEngine.export_table`
(Sprint 20), lui-même adossé à
`cabinet_os.reports.exporters.CsvReportExporter` (Sprint 9). Le
même endpoint accepte `export_format=json` (démontré par
`tests/integration/cloud_operations/
test_cloud_operations_sprint22_api.py::test_export_incidents_as_json`).
