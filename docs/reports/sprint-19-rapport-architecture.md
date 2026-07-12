# Rapport d'architecture — Sprint 19 (Enterprise Identity & Trust Platform)

## Résumé

Le Sprint 19 ajoute `backend/src/tmis/identity_platform/` (32
sous-modules, une couche API de 35+ endpoints) et migre 5 points
d'entrée sensibles de modules existants pour démontrer le passage
effectif par la plateforme. Points de contact hors
`identity_platform/` :

- `tmis/api/v1/router.py` — branchement du nouveau routeur REST
  (`identity_platform_router`), même patron que chaque sprint
  précédent.
- `tmis/workflow_automation/api/routes.py` — `decide_approval` appelle
  `authorize_or_403` avant la décision (`Permission.
  CONSULTATION_VALIDATE`, obligatoire).
- `tmis/ai_governance/api/routes.py` — `decide_validation` appelle
  `authorize_or_403` avant la décision (`Permission.
  STRATEGY_DRAFT_VALIDATE`, obligatoire).
- `tmis/cabinet_knowledge/api/routes.py` — `decide_validation_request`
  appelle `authorize_or_403` après le parsing de la décision, avant la
  mutation (`Permission.CONSULTATION_VALIDATE`, obligatoire).
- `tmis/integration_hub/api/{routes,schemas}.py` —
  `ConnectorConfigurationRequest.actor_id` (nouveau champ optionnel) ;
  `set_connector_configuration` appelle `authorize_or_403` uniquement
  si fourni (`Permission.ORGANIZATION_MANAGE`, opt-in).
- `tmis/ai_team/api/{routes,schemas}.py` —
  `MissionCreateRequest.requested_by` (nouveau champ optionnel) ;
  `launch_mission` appelle `authorize_or_403` uniquement si fourni
  (`Permission.AI_MODEL_RESTRICTED_USE`, opt-in).
- `tmis/identity_platform/secret_manager/engine.py` —
  `SecretManagerEngine.list_for_firm` ajouté (retourne les métadonnées
  d'un secret, jamais le clair), nécessaire à l'API `GET /secrets` et
  au tableau de bord.
- `tmis/identity_platform/session_manager`,
  `device_trust`, `mfa`, `delegation`, `policy_engine` — chaque store
  a reçu une méthode `list_for_firm`/`list_active_for_firm` (en plus
  des méthodes déjà scoping par utilisateur/permission) pour
  alimenter `monitoring.IdentityDashboard` sans dupliquer d'état.
- Quatre tests d'intégration existants (`test_workflow_automation_
  api_integration.py`, `test_ai_governance_api_integration.py`,
  `test_cabinet_knowledge_api_integration.py`,
  `test_cabinet_knowledge_api_remaining_endpoints.py`) ont été mis à
  jour pour assigner un rôle `PARTNER` à l'acteur de test avant
  d'appeler un endpoint désormais protégé — sans quoi ces tests
  échoueraient avec 403 au lieu du comportement attendu. Aucun autre
  test préexistant n'a été modifié : les 1570 tests des Sprints 1-18
  passent inchangés.

## Conformité aux principes architecturaux

- **Clean Architecture / DDD / SOLID** : chaque sous-module suit le
  patron `schemas.py` → `ports.py` (si un point d'extension est
  plausible) → `store.py` → `engine.py` → `__init__.py`. `tenant_context`
  et `risk_engine` n'ont pas de `store.py` propre pour la partie qu'ils
  réexportent/composent depuis `platform.*`.
- **Zero Trust** : `authorization.AuthorizationEngine.check()` ne
  retourne jamais un accord implicite — vérifié par
  `test_zero_trust_check_never_implicitly_allows_unknown_identity` et
  `test_unknown_identity_is_denied_by_default` (API).
- **Event Driven Architecture** : `security_events.SecurityEventBus`
  est un bus standalone (même patron que `WorkflowEventBus`/
  `IntegrationEventBus`), avec `subscribe_all` en plus — utilisé par
  `audit.SecurityAuditEngine` pour construire un trail complet sans
  s'abonner à chaque type d'événement individuellement.
- **Aucun module ne bypass la plateforme** : vérifié structurellement
  pour les 5 points d'entrée migrés (voir
  docs/109-guide-migration-identity-platform.md) et démontré par
  `tests/integration/identity_platform/
  test_identity_platform_migration_integration.py` (403 sans rôle,
  200 avec rôle, pour chacun).
- **Isolation multi-tenant démontrée par les tests** : voir
  `tests/integration/identity_platform/
  test_identity_platform_multi_tenant_isolation_integration.py` — 5
  tests couvrant organisations, rôles, autorisation, appareils/
  sessions/délégations/secrets et tableau de bord.

## Rapport de migration par module cité par le sprint

| Module | État de migration | Détail |
|---|---|---|
| **AI Kernel** (`tmis.ai`) | Non applicable | Socle IA sans endpoints REST propres (voir `tmis.ai.kernel.TMISKernel`) — n'a pas de point d'entrée HTTP à protéger directement. Tout futur agent appelant le Kernel passera par le point d'entrée métier qui l'invoque, déjà couvert par la migration de ce module. |
| **AI Team** (`tmis.ai_team`) | Migré (représentatif) | `POST /missions` (`launch_mission`) protégé en mode opt-in (`requested_by`). Endpoints restants (`create_team`, `run_mission`, `record_human_decision`, ...) suivent le même schéma au fil de leurs prochaines évolutions. |
| **Workflow Automation** (`tmis.workflow_automation`) | Migré (représentatif) | `POST /approvals/{id}/decide` protégé obligatoirement. Endpoints restants (`create_workflow`, `activate_workflow`, ...) suivent le même schéma. |
| **Knowledge Engine** (`tmis.cabinet_knowledge`) | Migré (représentatif) | `POST /validation-requests/{id}/decide` protégé obligatoirement. Endpoints restants suivent le même schéma. |
| **Marketplace** (`tmis.platform_sdk.marketplace`, `tmis.ai_team.marketplace`) | Non migré ce sprint | Aucun endpoint marketplace n'a de contrat d'API portant déjà un identifiant d'acteur exploitable sans changement de schéma ; suit le même schéma opt-in que `integration_hub`/`ai_team` lors d'une prochaine évolution. |
| **Integration Hub** (`tmis.integration_hub`) | Migré (représentatif) | `PUT /connectors/{id}/configuration` protégé en mode opt-in (`actor_id`). Endpoints restants (`enable_connector`, `disable_connector` — non tenant-scopés dans leur contrat actuel, `create_sync_job`, ...) suivent le même schéma ; `enable_connector`/`disable_connector` nécessitent d'abord de rendre le registre de connecteurs tenant-scopé, hors périmètre de ce sprint. |
| **AI Governance** (`tmis.ai_governance`) | Migré (représentatif) | `POST /validations/{id}/decide` protégé obligatoirement. Endpoints restants suivent le même schéma. |

## Décision structurante : obligatoire vs opt-in

Les endpoints qui portaient déjà un identifiant d'acteur dans leur
contrat d'API (`approver_id`, `reviewer`) ont reçu une vérification
**obligatoire** — aucun changement de schéma, effet immédiat. Les
endpoints qui n'en portaient aucun (`integration_hub`, `ai_team`) ont
reçu un champ optionnel additif : casser leur contrat existant avec un
champ requis aurait rompu tout appelant existant sans bénéfice
proportionné pour ce sprint. Voir
docs/109-guide-migration-identity-platform.md pour le détail complet
et le mode d'emploi pour migrer un futur endpoint.

## Dette technique identifiée

Voir docs/103-architecture-identity-platform.md — incompatibilité
`bcrypt`/`passlib` dans l'environnement (préexistante, non exercée par
ce sprint, à corriger avant qu'un futur sprint introduise une
authentification par mot de passe réel).

## Vérification finale

```
$ .venv/bin/ruff check src/ tests/
All checks passed!

$ .venv/bin/mypy src/
Success: no issues found in 1491 source files

$ .venv/bin/pytest -q
1639 passed, 4 skipped
```

1639 tests passent (1570 hérités des Sprints 1-18, inchangés + 69
nouveaux dédiés à `identity_platform` : 47 unitaires couvrant les 32
sous-modules par grappes, 22 d'intégration couvrant l'API REST,
l'isolation multi-tenant, la chaîne Zero Trust et la migration des 5
endpoints représentatifs).
