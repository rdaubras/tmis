# Référence API — SaaS Business Platform (Sprint 20)

Base path : `/api/v1/business-platform`. Toutes les mutations
sensibles exigent `Permission.BUSINESS_PLATFORM_MANAGE` via
`identity_platform.api.guard.authorize_or_403` (403 si l'appelant n'a
pas le rôle requis — voir docs/103-architecture-identity-platform.md).

| Méthode | Chemin | Description | Authentifié |
|---|---|---|---|
| GET | `/plans` | Liste le catalogue de plans actifs | non |
| POST | `/subscriptions/trial` | Démarre un essai gratuit | non |
| POST | `/subscriptions/{firm_id}/activate` | Active l'abonnement | oui |
| POST | `/subscriptions/{firm_id}/change-plan` | Change de plan | oui |
| GET | `/subscriptions/{firm_id}` | Consulte l'abonnement | non |
| POST | `/licenses/{firm_id}/assign` | Assigne une licence | oui |
| POST | `/licenses/{firm_id}/{grant_id}/revoke` | Révoque une licence | oui |
| GET | `/licenses/{firm_id}` | Liste les licences actives | non |
| GET | `/quotas/{firm_id}/{dimension}` | Consulte la limite d'une dimension | non |
| POST | `/quotas/{firm_id}/override` | Ajoute un override de quota | oui |
| POST | `/feature-flags/{key}/evaluate` | Évalue un flag pour un contexte | non |
| GET | `/usage/{firm_id}` | Instantané de consommation (7 dimensions) | non |
| GET | `/modules/{firm_id}` | État de chaque bounded context | non |
| POST | `/modules/{firm_id}/{module}/activate` | Active un module | oui |
| POST | `/modules/{firm_id}/{module}/deactivate` | Désactive un module | oui |
| GET | `/tenant-settings/{firm_id}` | Consulte les paramètres du cabinet | non |
| PUT | `/tenant-settings/{firm_id}` | Met à jour les paramètres | non |
| GET | `/analytics/{firm_id}` | Dashboard commercial | non |
| POST | `/reports/{firm_id}/generate` | Génère un rapport figé | non |
| GET | `/customer-portal/{firm_id}` | Instantané agrégé du portail client | non |

Les schémas de requête/réponse sont définis dans
`tmis.business_platform.api.schemas` (Pydantic) ; l'implémentation
dans `tmis.business_platform.api.routes`. OpenAPI est généré
automatiquement par FastAPI (`/docs`, `/openapi.json`).

## Codes d'erreur

- `404` : ressource introuvable (`firm_id` sans abonnement, licence
  ou dimension inconnue).
- `409` : action refusée par l'état métier (ex. module non actif
  pour ce cabinet, voir docs/116-guide-migration-business-platform.md).
- `422` : valeur d'énumération invalide (`license_type`, `dimension`,
  `environment`).
- `429` : quota dépassé (`AI_CALLS`, `WORKFLOWS`, ...).
- `403` : autorisation refusée par l'EITP.

## Voir aussi

docs/111-architecture-business-platform.md.
