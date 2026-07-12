# Guide — Application des quotas et feature flags aux modules existants (Sprint 20)

## Principe

Chaque module métier de TMIS peut désormais interroger la SaaS
Business Platform avant d'agir : `business_platform.quotas.
BusinessQuotaEngine` pour les limites dérivées du plan, `business_
platform.modules.ModuleRegistry` pour savoir si un bounded context
est activé pour un cabinet, `business_platform.feature_flags.
BusinessFeatureFlagEngine` pour les bascules fines (environnement,
groupe, fenêtre temporelle, expérimentation). Ces trois moteurs sont
accessibles via les singletons de `business_platform.bootstrap` —
aucune logique de quota/flag ne doit être dupliquée ailleurs.

## Quatre endpoints migrés ce sprint (représentatifs)

| Module | Endpoint | Mécanisme | Mode |
|---|---|---|---|
| `ai_fabric` | `POST /route` | `BusinessQuotaEngine.check_ai_calls` (`AI_CALLS`) | Obligatoire, dégradation gracieuse |
| `workflow_automation` | `POST /executions/start` | `BusinessQuotaEngine.check` (`WORKFLOWS`) | Obligatoire, dégradation gracieuse |
| `integration_hub` | `PUT /connectors/{id}/configuration` | `ModuleRegistry.is_active` (`INTEGRATION_HUB`) | Obligatoire, dégradation gracieuse |
| `cabinet_knowledge` | `POST /objects/{id}/quality` | `BusinessFeatureFlagEngine.is_enabled` (flag semé ouvert) | Kill switch, ouvert par défaut |

**Obligatoire, dégradation gracieuse** : les trois premiers endpoints
portaient déjà `firm_id` dans leur contrat — la vérification est donc
appelée systématiquement. Mais `SubscriptionEngine.get(firm_id)` lève
un `KeyError` si le cabinet n'a pas encore d'abonnement Business
Platform (le cas de la quasi-totalité des cabinets de test créés
avant ce sprint, et de tout cabinet qui n'a pas encore été
"onboardé" commercialement). Ce `KeyError` est explicitement capturé
et la vérification silencieusement ignorée dans ce cas — un cabinet
sans abonnement n'est pas encore soumis aux quotas/modules de la
SaaS Business Platform. Dès qu'un cabinet démarre un abonnement
(`SubscriptionEngine.start_trial` + `activate`), l'application
devient effective sans aucun changement de code — démontré par
`tests/integration/business_platform/test_business_platform_
enforcement_integration.py`.

**Kill switch, ouvert par défaut** : `cabinet_knowledge`'s quality
evaluation endpoint n'avait auparavant aucune notion de flag. Un flag
fraîchement créé dans `platform.feature_flags.FeatureFlagEngine` est
**fermé** par défaut (aucune allow-list, `rollout_percentage=0`) — le
brancher tel quel aurait cassé l'endpoint pour tout appelant existant.
`business_platform.bootstrap.get_business_feature_flag_engine` sème
donc explicitement `cabinet_knowledge.quality_evaluation` avec
`enabled=True, rollout_percentage=100.0` : le comportement observable
ne change pas aujourd'hui, mais l'administrateur dispose désormais du
point d'intégration réel pour restreindre l'accès par environnement,
groupe, fenêtre temporelle ou expérimentation sans toucher au code.

## Pourquoi quatre et pas tous les endpoints

Comme pour la migration EITP du Sprint 19 (voir docs/109-guide-
migration-identity-platform.md), appliquer des quotas/flags à chaque
endpoint sensible de TMIS en un seul sprint referait le travail de
plusieurs sprints à la fois. Ce sprint établit le mécanisme (moteurs
+ singletons + les deux patrons d'intégration — dégradation gracieuse
pour les quotas/modules, kill switch semé ouvert pour les flags) et le
démontre sur un échantillon couvrant les quatre modules explicitement
cités par le sprint (`ai_fabric`, `workflow_automation`,
`cabinet_knowledge`, `integration_hub`). La migration du reste des
endpoints suit le même schéma au fil des évolutions de chaque module.

## Comment migrer un nouvel endpoint

1. **Quota** : si l'endpoint porte déjà `firm_id` et correspond à une
   des sept dimensions de `quotas.schemas.QuotaDimension`, appeler
   `BusinessQuotaEngine.check_ai_calls`/`check` avant l'action,
   capturer `KeyError` pour ne pas bloquer un cabinet non onboardé,
   renvoyer 429 si `not result.allowed`.
2. **Module** : si l'endpoint relève d'un bounded context listé dans
   `modules.schemas.TmisModule`, appeler `ModuleRegistry.is_active`
   avant l'action, même dégradation gracieuse (`KeyError` → ignoré),
   renvoyer 409 si le module est inactif.
3. **Feature flag** : pour une bascule fine sur un endpoint
   *existant*, semer le flag `enabled=True, rollout_percentage=100.0`
   dans `business_platform.bootstrap` avant de l'utiliser — un flag
   non semé est fermé par défaut et casserait tout appelant existant.
   Pour une fonctionnalité *nouvelle*, un flag fermé par défaut est au
   contraire le comportement voulu (dark launch).
4. Mettre à jour les tests existants qui exercent cet endpoint pour
   qu'ils créent un abonnement Business Platform (`get_subscription_
   engine().start_trial(...)` + `.activate(...)`) uniquement s'ils
   veulent exercer l'enforcement — sinon le comportement par défaut
   (non onboardé = non gated) suffit et aucun test existant n'a besoin
   d'être modifié, ce que ce sprint a vérifié sur les 1639 tests
   existants (aucune régression).

## Migration report complet — voir aussi

`docs/reports/sprint-20-rapport-architecture.md` recense l'état de
migration de chaque module cité par le sprint.
