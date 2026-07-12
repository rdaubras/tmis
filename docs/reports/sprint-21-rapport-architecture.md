# Rapport d'architecture — Sprint 21 (Cloud Operations & Observability Platform)

## Résumé

Le Sprint 21 ajoute `backend/src/tmis/cloud_operations/` (20
sous-modules, une couche API de 21 endpoints) et instrumente 3 points
d'entrée représentatifs de modules existants pour démontrer une
publication réelle de télémétrie. Points de contact hors
`cloud_operations/` :

- `tmis/main.py` — branchement du nouveau routeur REST
  (`cloud_operations_router`), monté directement sur `app`, hors
  `/api/v1`, à côté de `platform_router` (Sprint 10).
- `tmis/platform/observability/middleware.py` — `metrics_middleware`
  publie désormais un `RESPONSE_TIME` et un span `SpanKind.API` sous
  le `trace_id` de chaque requête (sauf les requêtes vers
  `/cloud-operations/*` lui-même, pour ne pas polluer ses propres
  métriques).
- `tmis/workflow_automation/execution_engine/engine.py` —
  `ExecutionEngine.start`/`_run_from` publient un `WORKFLOW_COUNT`,
  un span `SpanKind.WORKFLOW` (fermé en succès ou en échec), et un
  `ErrorEvent` en cas d'échec.
- `tmis/workflow_automation/execution_engine/schemas.py` — ajout du
  champ `WorkflowExecution.telemetry_span_id` (optionnel), pour que
  `_run_from` puisse fermer le span ouvert par `start` sans second
  lookup.
- `tmis/ai_fabric/router/engine.py` — `RouterEngine.route` publie un
  `AI_CALL_DURATION` (latence de la décision de routage) et un
  `ErrorEvent` sur `NoEligibleModelError`/`QuotaExceededError`.
- `tests/integration/platform/test_platform_api_integration.py` —
  `test_platform_health_ready_reports_component_statuses` mis à jour
  (`>= 7` au lieu de `== 7`) puisque `cloud_operations.health_checks`
  enregistre 5 vérifications supplémentaires dans le même
  `platform.health.HealthCheckEngine` partagé.

## Conformité aux principes architecturaux

- **Clean Architecture / DDD / SOLID** : chaque sous-module suit le
  patron `schemas.py` → `ports.py` (si un point d'extension est
  plausible) → `store.py` → `engine.py` → `__init__.py`. Les modules
  purement compositionnels ou à état transitoire (`capacity`,
  `performance`, `health_checks`, `diagnostics`, `runbooks`, `cache`,
  `queue_monitoring`) n'ont ni `ports.py` ni `store.py` propre.
- **Composer, ne jamais reconstruire** : voir la table complète dans
  docs/118-architecture-cloud-operations.md — neuf compositions
  explicites vers des moteurs des Sprints 1, 8, 10, 14, 18, 19, 20.
  Confirmé par recherche directe qu'aucun circuit breaker, aucun
  suivi hit/miss de cache, aucun suivi taille/débit de file
  n'existait ailleurs dans TMIS avant ce sprint — ces trois modules
  sont des constructions authentiquement nouvelles.
- **Event Driven Architecture** : `MetricEvent`, `AlertEvent`,
  `SLASample`, `ErrorEvent`, `TelemetryEvent`, `ProfilingSample` sont
  tous des enregistrements append-only historisés — même philosophie
  que `business_platform.metering.MeteringEvent` (Sprint 20).
- **OpenTelemetry comme abstraction** : `telemetry.TelemetryEngine`
  reproduit l'API OpenTelemetry sans en dépendre, remplaçable plus
  tard par un vrai SDK sans changer un seul appelant — voir
  docs/119-guide-opentelemetry-cloud-operations.md.
- **Isolation multi-tenant** : chaque événement historisé porte un
  `firm_id | None` optionnel ; `None` signifie une donnée
  plateforme-globale, jamais une fuite entre cabinets.
- **Zero Trust / sécurité** : `chaos_testing.ChaosTestingEngine` lève
  `ProductionChaosTestingForbiddenError` si `environment ==
  "production"` et `authorized=False` — vérifié par
  `tests/unit/cloud_operations/test_resilience_chaos.py` et par
  l'API (`POST /cloud-operations/chaos/{scenario}` → 403).
- **Aucune donnée sensible dans les logs** : `logging.
  LoggingGovernanceEngine.redact` compose directement `platform.
  logging.redaction.RedactSensitiveFields` (Sprint 10), jamais une
  seconde implémentation d'anonymisation.

## Rapport d'instrumentation par module cité par le sprint

| Module | État d'instrumentation | Détail |
|---|---|---|
| **API** (`platform.observability.middleware`) | Instrumenté (représentatif) | Chaque requête HTTP publie `RESPONSE_TIME` + un span `API` sous le `trace_id` de la requête. |
| **Workflow** (`workflow_automation.execution_engine`) | Instrumenté (représentatif) | `WORKFLOW_COUNT` + span `WORKFLOW` à chaque exécution ; `ErrorTrackingEngine` sur échec. |
| **AI Fabric** (`ai_fabric.router`) | Instrumenté (représentatif) | `AI_CALL_DURATION` sur chaque décision de routage ; `ErrorTrackingEngine` sur modèle indisponible/quota dépassé. |
| **Agents, Knowledge Engine, Connecteurs** | Non instrumenté ce sprint | Suit le même schéma documenté (docs/124-guide-migration-cloud-operations.md) lors d'une prochaine évolution — même principe que les migrations partielles des Sprints 19/20. |

## Décision structurante : imports locaux pour éviter les cycles

`cloud_operations.bootstrap` compose à son tour `ai_fabric.bootstrap`,
`workflow_automation.bootstrap`, `integration_hub.bootstrap`,
`identity_platform.bootstrap`, `business_platform.bootstrap`,
`platform_sdk.bootstrap`. Si `workflow_automation.execution_engine`
importait `cloud_operations.bootstrap` en haut de fichier, le module
`workflow_automation.bootstrap` (importé transitivement par
`cloud_operations.bootstrap`) tenterait de réimporter
`workflow_engine.engine` avant sa propre initialisation complète —
un cycle d'import classique. Chaque point d'instrumentation importe
donc `cloud_operations.bootstrap` **localement**, à l'intérieur de la
méthode qui en a besoin, ce qui différe la résolution du cycle
jusqu'au premier appel réel (après que tous les modules soient
chargés) — vérifié par le boot complet de l'application FastAPI et
par l'exécution de la suite de tests complète sans erreur d'import.

## Dette technique identifiée

Aucune nouvelle dette introduite par ce sprint. L'instrumentation des
modules restants (Agents, Knowledge Engine, Connecteurs et le reste
de `ai_fabric`/`workflow_automation`) suit le même schéma documenté et
n'est pas une dette cachée : c'est un choix de séquençage, comme pour
les migrations des Sprints 19/20. La persistance/API du « Module
Document » (ancien Sprint 21, désormais Sprint 22 après la révision
de roadmap de ce sprint) reste également non livrée — proposée comme
priorité du prochain sprint ci-dessous.

## Vérification finale

```
$ .venv/bin/ruff check src/
All checks passed!

$ .venv/bin/mypy src/
Success: no issues found in 1654 source files

$ .venv/bin/pytest -q
1727 passed, 4 skipped
```

1727 tests passent (1691 hérités des Sprints 1-20, un seul ajusté
pour refléter les 5 nouvelles vérifications de santé + 36 nouveaux
dédiés à `cloud_operations` : 28 unitaires couvrant les 20
sous-modules par grappes, 8 d'intégration couvrant l'API REST, le
traçage bout-en-bout via une vraie requête HTTP, le verrou de
production du chaos testing, et le cycle de vie complet d'un
incident).
