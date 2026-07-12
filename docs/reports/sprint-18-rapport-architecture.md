# Rapport d'architecture — Sprint 18 (Legal Integration Hub)

## Résumé

Le Sprint 18 ajoute `backend/src/tmis/integration_hub/` (19
sous-modules, 7 connecteurs de référence, une couche API) au-dessus du
socle existant. Aucun module métier des Sprints 2-17 n'a été modifié
en profondeur ; deux points de contact minimaux hors
`integration_hub/` :

- `tmis/api/v1/router.py` — branchement du nouveau routeur REST
  (`integration_hub_router`), même patron que chaque sprint précédent.
- `tmis.integration_hub.connector_framework.ports.ConnectorPort.authenticate`
  — un correctif de signature (`-> None` → `-> bool`), détecté par
  mypy pendant le développement de ce même sprint : toutes les
  implémentations (connecteurs de référence, `BaseConnector`,
  `InMemoryFakeConnector`) retournaient déjà un booléen, seule la
  déclaration du Protocol était incorrecte.

## Conformité aux principes architecturaux

- **Clean Architecture / DDD / SOLID / API First** : chaque
  sous-module suit le patron `schemas.py` → `ports.py` (si un point
  d'extension est plausible) → implémentation(s) → composition dans
  `integration_hub/bootstrap.py`. `security/` et `health/` n'ont
  délibérément pas de `schemas.py` propre : ils composent
  intégralement les types de `platform.security`/
  `platform.rate_limiting`/`platform.health`.
- **Event Driven Architecture** : `event_bridge.IntegrationEventBus`
  est un bus standalone (même patron que
  `CollaborationEventBus`/`GovernanceEventBus`/`WorkflowEventBus`) ;
  `EventBridge` fait explicitement le pont vers
  `workflow_automation.event_bus.WorkflowEventBus`.
- **Aucune logique métier propre à un fournisseur dans le LIH** :
  vérifié structurellement — `connector_framework.ConnectorPort` ne
  connaît que `authenticate`/`read`/`write`, génériques ; les 7
  connecteurs de référence (`connectors/`) sont des implémentations de
  démonstration en mémoire, explicitement documentées comme
  remplaçables sans modifier le reste du système.
- **Toutes les communications externes sont sécurisées** : chiffrées
  (`security.encrypt_config`), authentifiées (`authentication`),
  signées (`webhooks.sign_payload`/`verify_signature`, HMAC-SHA256),
  journalisées (`monitoring`), isolées par tenant
  (`security.require_tenant`) — vérifié par
  `test_authentication_security.py`,
  `test_event_bridge_webhooks.py`.
- **Toutes les synchronisations sont configurables** : `SyncJobConfig`
  paramètre direction, mode, stratégie de conflit par job ; `mapping`
  paramètre la correspondance de champs par (connecteur, cabinet, type
  d'entité).

## Décision structurante : deux "connecteurs" au sens différent

`platform_sdk.connector_sdk.BaseConnectorPlugin` (Sprint 13) et
`integration_hub.connector_framework.ConnectorPort` (Sprint 18)
portent le même rôle architectural ("un connecteur") mais des
périmètres disjoints — le premier est un plugin de recherche seule lié
au Plugin System (`PluginContext`, pagination, cache), le second un
contrat CRUD complet, tenant par tenant, gouverné par
`authentication`/`security`, jamais à travers le Plugin System.
Documenté explicitement (docstring de `ConnectorPort`,
`docs/97-architecture-integration-hub.md`) plutôt que renommé — même
principe déjà acté pour `GovernanceEngine`/`PolicyEngine` et les
quatre "Workflow" de TMIS.

## Décision structurante : réutilisation vs réimplémentation

Trois réutilisations directes (aucune réimplémentation) :

- `security.IntegrationSecurityEngine` compose
  `platform.security.encryption`/`secrets_rotation`/`tenant_isolation`
  et `platform.rate_limiting` (Sprint 10).
- `health.register_connector_health_checks` compose
  `platform.health.HealthCheckEngine`/`CallableHealthCheck` (Sprint 10).
- `conflict_resolution.HumanValidationStrategy` compose
  `ai_governance.human_validation.HumanValidationEngine` (Sprint 15).

Trois réimplémentations délibérées (même patron, code local) :

- `queue.InMemorySyncQueue` — forme de `ai_team.work_queue`.
- `retry.IntegrationRetryPolicy` — forme de
  `workflow_automation.retry`/`ai_fabric.retry`.
- `sandbox.ConnectorSandbox` — *patron* seulement (quota + timeout) de
  `platform_sdk.sandbox.SandboxExecutor`, dont l'implémentation réelle
  est trop couplée aux internes du Plugin System pour être réutilisée
  telle quelle.

## Vérification

- `ruff check src tests` : aucune erreur (1348+ fichiers)
- `mypy src` : aucune erreur
- `pytest -q --cov=tmis --cov-fail-under=90` : 1570 tests passés, 4
  ignorés (préexistants, sans rapport avec ce sprint), couverture
  globale 95,81 % ; 97 % sur `tmis.integration_hub` seul (92 tests
  dédiés)
- Démarrage de l'application FastAPI vérifié via `TestClient` :
  19 endpoints REST testés bout en bout (connecteurs, configuration,
  synchronisation, webhooks signés, santé)

## Dette et limites connues

- Le déclenchement de `EventBridge`/`WebhookEngine` au démarrage
  repose sur le premier appel à `get_webhook_engine()` (composition
  paresseuse `@lru_cache`) plutôt que sur un hook de démarrage
  explicite de l'application — cohérent avec le reste de TMIS, mais à
  surveiller si un jour un événement doit être publié avant la
  première requête HTTP.
- `LoggingWebhookSender` journalise au lieu d'émettre un vrai appel
  HTTP sortant — un déploiement réel doit fournir un
  `WebhookSenderPort` basé sur `httpx` (ou équivalent) avant mise en
  production des webhooks sortants.
- Aucune boucle de fond n'exécute `scheduler.due()` ni ne consomme
  `queue` automatiquement dans ce sprint — un futur processus (Celery
  ou équivalent) devra les piloter périodiquement, comme déjà noté
  pour `workflow_automation.scheduler` au Sprint 17.
