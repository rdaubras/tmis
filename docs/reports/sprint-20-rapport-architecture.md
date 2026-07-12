# Rapport d'architecture — Sprint 20 (SaaS Business Platform)

## Résumé

Le Sprint 20 ajoute `backend/src/tmis/business_platform/` (20
sous-modules, une couche API de 20 endpoints) et migre 4 points
d'entrée sensibles de modules existants pour démontrer l'application
effective des quotas/modules/feature flags. Points de contact hors
`business_platform/` :

- `tmis/api/v1/router.py` — branchement du nouveau routeur REST
  (`business_platform_router`), même patron que chaque sprint
  précédent.
- `tmis/identity_platform/permissions/schemas.py` — ajout de
  `Permission.BUSINESS_PLATFORM_MANAGE`, accordée par défaut aux
  rôles `PARTNER` et `IT_ADMIN` (`tmis/identity_platform/rbac/
  schemas.py`), utilisée par les mutations sensibles de l'API
  Business Platform.
- `tmis/platform/licensing/bootstrap.py` — extraction de
  `get_license_key_signer()` (nouveau singleton) pour que
  `business_platform.licenses.LicenseEngine` et
  `platform.licensing.LicenseEngine` signent avec le même secret.
- `tmis/platform/cost_control/bootstrap.py` — extraction de
  `get_cost_entry_store()` (nouveau singleton) pour que
  `business_platform.analytics.AnalyticsEngine` lise les entrées de
  coût directement, sans dupliquer le suivi déjà tenu par
  `CostTrackerEngine`.
- `tmis/ai_fabric/api/routes.py` — `route_request` (`POST /route`)
  appelle `BusinessQuotaEngine.check_ai_calls` avant de router
  l'appel (429 si dépassé, obligatoire mais dégradation gracieuse si
  le cabinet n'a pas d'abonnement Business Platform).
- `tmis/workflow_automation/api/routes.py` — `start_execution`
  (`POST /executions/start`) appelle `BusinessQuotaEngine.check` sur
  la dimension `WORKFLOWS` avant de démarrer l'exécution, même patron.
- `tmis/integration_hub/api/routes.py` — `set_connector_configuration`
  (`PUT /connectors/{id}/configuration`) appelle `ModuleRegistry.
  is_active` sur `TmisModule.INTEGRATION_HUB` (409 si inactif, même
  dégradation gracieuse).
- `tmis/cabinet_knowledge/api/routes.py` — `evaluate_quality`
  (`POST /objects/{id}/quality`) appelle `BusinessFeatureFlagEngine.
  is_enabled` sur un flag semé ouvert par défaut
  (`CABINET_KNOWLEDGE_QUALITY_FLAG_KEY`, voir
  docs/116-guide-migration-business-platform.md).

## Conformité aux principes architecturaux

- **Clean Architecture / DDD / SOLID** : chaque sous-module suit le
  patron `schemas.py` → `ports.py` (si un point d'extension est
  plausible) → `store.py` → `engine.py` → `__init__.py`. Les modules
  purement compositionnels (`billing`, `invoicing`, `payments`,
  `pricing`, `usage`, `trial`) n'ont ni `ports.py` ni `store.py`.
- **Composer, ne jamais réimplémenter** : voir la table complète dans
  docs/111-architecture-business-platform.md — onze compositions
  explicites vers des moteurs des Sprints 8, 9, 10, 13, 14 et 19.
- **Event Driven Architecture** : `metering.MeteringEvent` est un
  enregistrement append-only historisé — même philosophie que
  `identity_platform.security_events`/`audit` (Sprint 19).
- **Aucun module ne bypass la plateforme** : vérifié structurellement
  pour les 4 points d'entrée migrés et démontré par
  `tests/integration/business_platform/
  test_business_platform_enforcement_integration.py` (200/429/409/403
  selon le scénario).
- **Isolation multi-tenant démontrée par les tests** : voir
  `tests/integration/business_platform/
  test_business_platform_multi_tenant_isolation_integration.py` — 3
  tests couvrant abonnements/quotas/modules, licences et usage.
- **Versionnement des plans sans rupture contractuelle** : vérifié
  par `test_publishing_new_version_never_mutates_previous` et
  `test_subscription_pins_exact_plan_version_sold`.

## Rapport de migration par module cité par le sprint

| Module | État de migration | Détail |
|---|---|---|
| **AI Fabric** (`tmis.ai_fabric`) | Migré (représentatif) | `POST /route` protégé par `BusinessQuotaEngine.check_ai_calls` (dimension `AI_CALLS`). Autres endpoints (`/plan`, `/compare`, ...) suivent le même schéma lors d'une prochaine évolution. |
| **Workflow Automation** (`tmis.workflow_automation`) | Migré (représentatif) | `POST /executions/start` protégé par `BusinessQuotaEngine.check` (dimension `WORKFLOWS`), avec enregistrement de la consommation via `MeteringEngine.record` après succès. |
| **Integration Hub** (`tmis.integration_hub`) | Migré (représentatif) | `PUT /connectors/{id}/configuration` protégé par `ModuleRegistry.is_active` (`TmisModule.INTEGRATION_HUB`). |
| **Knowledge Engine** (`tmis.cabinet_knowledge`) | Migré (représentatif) | `POST /objects/{id}/quality` protégé par un feature flag semé ouvert, patron distinct des trois précédents (kill switch vs quota/module). |

## Décision structurante : dégradation gracieuse vs kill switch ouvert

Les vérifications de quota/module s'appuient sur `SubscriptionEngine.
get(firm_id)`, qui lève `KeyError` pour tout cabinet sans abonnement
Business Platform — le cas de la quasi-totalité des cabinets de test
antérieurs à ce sprint. Ce `KeyError` est explicitement capturé et la
vérification silencieusement ignorée : un cabinet non onboardé n'est
pas encore soumis aux quotas/modules commerciaux. Le feature flag de
`cabinet_knowledge`, à l'inverse, n'a aucune notion d'abonnement —
il est donc semé `enabled=True, rollout_percentage=100.0` au
démarrage pour préserver le comportement observable existant. Voir
docs/116-guide-migration-business-platform.md pour le détail complet.

## Dette technique identifiée

Aucune nouvelle dette introduite par ce sprint. La migration des
endpoints restants de `ai_fabric`/`workflow_automation`/
`integration_hub`/`cabinet_knowledge`, ainsi que celle des autres
modules non cités par le sprint (`ai_team`, `ai_governance`,
`strategic_intelligence`, `cabinet_os`), suit le même schéma
documenté et n'est pas une dette cachée : c'est un choix de
séquençage, comme pour la migration EITP du Sprint 19.

## Vérification finale

```
$ .venv/bin/ruff check src/ tests/
All checks passed!

$ .venv/bin/mypy src/
Success: no issues found in 1570 source files

$ .venv/bin/pytest -q
1691 passed, 4 skipped
```

1691 tests passent (1639 hérités des Sprints 1-19, inchangés + 52
nouveaux dédiés à `business_platform` : 40 unitaires couvrant les 20
sous-modules par grappes, 12 d'intégration couvrant l'API REST, le
parcours client complet, l'application des quotas/modules/flags sur
les 4 endpoints migrés, et l'isolation multi-tenant).
