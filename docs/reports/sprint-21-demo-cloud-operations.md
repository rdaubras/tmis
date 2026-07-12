# Démo — Sprint 21 (Cloud Operations & Observability Platform)

Démonstration exécutée via `TestClient(app)` contre l'API réelle
(`/api/v1/business-platform`, `/cloud-operations`) et les singletons
`cloud_operations.bootstrap` — sortie capturée telle quelle.

## 1. Une requête HTTP réelle publie un span API sous son trace_id

```
GET /api/v1/business-platform/plans -> 200, trace_id=4164cd60-90e9-4848-b43c-52fdfd6e5234
```

Le `trace_id` provient de `core.observability.trace_id_middleware`
(Sprint 1) ; `platform.observability.metrics_middleware` publie
désormais un `RESPONSE_TIME` et un span `API` sous cet id — voir
docs/124-guide-migration-cloud-operations.md.

## 2. Un appel AI Fabric sous le même trace_id complète la trace

```
Modèle retenu par le router : claude-legal
```

`ai_fabric.router.RouterEngine.route` publie automatiquement un
`AI_CALL_DURATION` à chaque décision — le span `AI_FABRIC` est ajouté
manuellement ici pour simuler le hop "Workflow → AI Fabric" du chemin
de requête sans avoir à construire un workflow complet dans la démo.

## 3. La trace complète — API → AI Fabric, un seul trace_id

```
[api       ] GET /api/v1/business-platform/plans (status=ok)
[ai_fabric ] route-model (status=ok)
```

`GET /cloud-operations/traces/{trace_id}` retourne l'arbre de spans
complet — la démonstration du suivi de bout en bout demandée par le
sprint. En production, l'instrumentation réelle de
`workflow_automation.execution_engine` (voir §1) insère
automatiquement le hop `WORKFLOW` entre `API` et `AI_FABRIC` quand un
workflow relaie le `trace_id` de la requête dans son `context`.

## 4. Métriques historisées : temps de réponse et durée d'appel IA

```
RESPONSE_TIME avg: 4.45 ms
AI_CALL_DURATION avg: 0.21 ms
```

`GET /cloud-operations/metrics/{category}` expose le même historique.

## 5. Health check — 12 composants (7 plateforme + 5 métier)

```
status=up, 12 composants:
   ['ai_fabric', 'ai_kernel', 'business_platform', 'cache', 'connectors',
    'database', 'event_bus', 'identity_platform', 'marketplace',
    'queue', 'storage', 'workflow_engine']
```

Les 7 premiers viennent de `platform.health.bootstrap` (Sprint 10) ;
`ai_fabric`, `marketplace`, `workflow_engine`, `identity_platform`,
`business_platform` sont les 5 nouvelles vérifications enregistrées
par `cloud_operations.health_checks` dans le **même** moteur partagé.

## 6. Dashboards overview

```
{'firm_id': None, 'platform_status': 'up', 'workflows_executed': 0,
 'integrations_healthy': 7, 'integrations_total': 7,
 'has_ai_view': False, 'has_security_view': False, 'has_business_view': False}
```

Sans `firm_id`, les vues IA/sécurité/business restent `None` — pas de
signification cross-cabinet pour ces trois dashboards.

## 7. Capacité — projection de croissance

```
Projection à 1 période : 70.0 (croissance 100.0%)
```

`CapacityEngine.forecast` projette la profondeur de file
`sync-queue` à partir de six échantillons historisés
(10, 15, 20, 25, 30, 35), en comparant la moyenne de la première
moitié à la seconde.

## 8. Incident — cycle de vie complet

```
Incident ouvert : inc-f7567b3ed73d (open)
Post-mortem : cause='Panne fournisseur', durée=0.00 min
```

`open_incident` → `track` (transition automatique vers
`INVESTIGATING`) → `resolve` → `record_post_mortem` — les quatre
étapes demandées par le sprint.

## 9. Runbook associé

```
1. Check the provider's public status page for an ongoing outage.
2. Confirm ai_fabric.fallback.FallbackEngine is routing to a backup.
3. Verify ai_fabric.retry.RetryPolicy is not exhausting retries.
4. If no fallback exists, disable the capability via feature flags.
5. Notify affected firms and open an incident.
```

Le runbook `ai-provider-unavailable` référence directement les
moteurs TMIS existants à consulter — pas une procédure abstraite.

## 10. Chaos testing — verrou production

```
Environnement dev : Forced circuit 'ai_fabric.provider' open to simulate ai_provider_outage
```

En environnement `development`, le scénario s'exécute librement. En
environnement `production` sans `authorized=true`,
`ChaosTestingEngine.run_scenario` lève
`ProductionChaosTestingForbiddenError` (`POST /cloud-operations/chaos/
{scenario}` renvoie 403) — vérifié explicitement par
`tests/unit/cloud_operations/test_resilience_chaos.py::
test_chaos_testing_forbidden_in_production_without_authorization` et
`tests/integration/cloud_operations/test_cloud_operations_api.py::
test_chaos_scenario_forbidden_in_production_without_authorization`.
