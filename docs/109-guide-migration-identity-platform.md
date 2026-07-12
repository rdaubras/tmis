# Guide — Migration des modules existants vers l'EITP (Sprint 19)

## Principe

Chaque module métier de TMIS construit depuis le Sprint 2 doit
récupérer le contexte utilisateur, récupérer le contexte tenant,
vérifier les permissions, appliquer les politiques du cabinet et
enregistrer des événements de sécurité avant toute action sensible.
Le point d'entrée unique est `identity_platform.api.guard.
authorize_or_403` :

```python
from tmis.identity_platform.api.guard import authorize_or_403
from tmis.identity_platform.permissions.schemas import Permission

authorize_or_403(firm_id, user_id, Permission.CONSULTATION_VALIDATE)
```

Cette fonction reste volontairement fine : elle résout le contexte
d'identité (`identity_context.get_or_default`), appelle le moteur
central (`authorization.AuthorizationEngine.check`) et lève une
`HTTPException(403)` si la décision est un refus. Aucune logique
d'autorisation ne vit ailleurs que dans `identity_platform` ;
`guard.py` ne fait que la glue HTTP.

## Cinq endpoints migrés ce sprint (représentatifs)

| Module | Endpoint | Permission | Mode |
|---|---|---|---|
| `workflow_automation` | `POST /approvals/{id}/decide` | `CONSULTATION_VALIDATE` | Obligatoire |
| `ai_governance` | `POST /validations/{id}/decide` | `STRATEGY_DRAFT_VALIDATE` | Obligatoire |
| `cabinet_knowledge` | `POST /validation-requests/{id}/decide` | `CONSULTATION_VALIDATE` | Obligatoire |
| `integration_hub` | `PUT /connectors/{id}/configuration` | `ORGANIZATION_MANAGE` | Optionnel (`actor_id`) |
| `ai_team` | `POST /missions` | `AI_MODEL_RESTRICTED_USE` | Optionnel (`requested_by`) |

**Obligatoire** : les trois premiers endpoints portaient déjà un champ
identifiant l'acteur (`approver_id`/`reviewer`) dans leur contrat
d'API existant — l'autorisation est donc devenue systématique sans
changement de schéma, immédiatement effective pour tout appelant.

**Optionnel** : les deux derniers endpoints ne portaient auparavant
aucune notion d'identité. Y ajouter un champ **obligatoire** aurait
cassé tout appelant existant (schéma API rétrocompatible = un ajout,
jamais un champ requis qui n'existait pas). `ConnectorConfigurationRequest.
actor_id`/`MissionCreateRequest.requested_by` sont donc des champs
optionnels (`str | None = None`) : l'autorisation ne s'active que si
l'appelant fournit une identité, ce qui laisse les intégrations
existantes fonctionner à l'identique tout en offrant, dès aujourd'hui,
le point d'intégration réel pour tout nouvel appelant qui fournit une
identité. Voir `tests/integration/identity_platform/
test_identity_platform_migration_integration.py` pour la démonstration
des deux modes.

## Pourquoi cinq et pas tous les endpoints

Migrer chaque endpoint sensible de TMIS (des dizaines à travers 18
sprints) en un seul sprint referait le travail de plusieurs sprints à
la fois et risquerait de casser une large part des 1500+ tests
existants sans les revoir un par un. Ce sprint établit le mécanisme
(`authorize_or_403`, deux patrons d'intégration — obligatoire vs
opt-in) et le démontre sur un échantillon couvrant les cinq modules
explicitement cités par le sprint (AI Kernel excepté — c'est un socle
IA sans endpoints REST propres, voir docs/09-roadmap-30-sprints.md
pour son rôle). La migration du reste des endpoints suit le même
schéma au fil des évolutions de chaque module — ce n'est pas une dette
cachée : c'est un choix de séquençage documenté.

## Comment migrer un nouvel endpoint

1. Identifier la `Permission` la plus proche du vocabulaire déjà
   défini dans `identity_platform.permissions.Permission` — ne pas en
   créer une nouvelle sans vérifier que l'existant ne convient pas.
2. Si l'endpoint porte déjà un identifiant d'acteur dans son contrat :
   appeler `authorize_or_403` avant la mutation, après toute validation
   de forme (422/400) mais avant toute vérification de ressource
   (404) — voir `cabinet_knowledge.api.routes.decide_validation_request`
   pour l'ordre exact (parse decision → authorize → lookup+mutate).
3. Si l'endpoint ne porte aucun identifiant d'acteur : ajouter un
   champ optionnel (`actor_id: str | None = None` ou nommé selon le
   domaine) et n'appeler `authorize_or_403` que s'il est fourni.
4. Mettre à jour les tests existants qui exercent cet endpoint pour
   qu'ils assignent un rôle via `identity_platform.bootstrap.
   get_role_engine().assign(firm_id, actor_id, Role.PARTNER)` avant
   l'appel — sinon l'appelant de test n'a aucun rôle et se voit
   refuser (403) au lieu du comportement attendu.

## Migration report complet — voir aussi

`docs/reports/sprint-19-rapport-architecture.md` recense l'état de
migration de chaque module cité par le sprint (AI Kernel, AI Team,
Workflow Automation, Knowledge Engine, Marketplace, Integration Hub,
AI Governance).
