# Référence API — Platform SDK (Sprint 13)

Base : `/api/v1/platform-sdk`. Documentation interactive complète sur
`/docs` (OpenAPI, généré automatiquement par FastAPI).

## Plugins & cycle de publication

| Méthode | Chemin | Rôle |
|---|---|---|
| `GET` | `/plugins/{plugin_id}` | détail d'un manifeste |
| `POST` | `/plugins/{plugin_id}/validate` | `DEVELOPMENT → VALIDATED` |
| `POST` | `/plugins/{plugin_id}/sign` | `VALIDATED → SIGNED` |
| `POST` | `/plugins/{plugin_id}/publish` | `SIGNED → PUBLISHED` |
| `POST` | `/plugins/{plugin_id}/retire` | `PUBLISHED → RETIRED` |
| `GET` | `/plugins/{plugin_id}/publishing-history` | historique complet des transitions |

Corps des requêtes `POST` : `{"actor": "...", "reason": "..." }`
(`reason` optionnel, utilisé par `retire`).

## Marketplace

| Méthode | Chemin | Rôle |
|---|---|---|
| `GET` | `/marketplace` | recherche (`query`, `plugin_type`) — uniquement les plugins publiés |
| `GET` | `/marketplace/categories` | types de plugins publiés |
| `POST` | `/marketplace/{plugin_id}/install` | `{"firm_id", "permissions": [...]}` |
| `POST` | `/marketplace/{plugin_id}/update` | `?firm_id=...` |
| `POST` | `/marketplace/{plugin_id}/uninstall` | `?firm_id=...` |
| `POST` | `/marketplace/{plugin_id}/reviews` | `{"firm_id", "rating", "comment"}` |
| `GET` | `/marketplace/{plugin_id}/reviews` | tous les avis d'un plugin |

## Extensions installées

| Méthode | Chemin | Rôle |
|---|---|---|
| `GET` | `/extensions` | `?firm_id=...` — toutes les extensions d'un cabinet |

## Developer Portal

| Méthode | Chemin | Rôle |
|---|---|---|
| `GET` | `/developer-portal` | `?type=...` ou `?keyword=...` |

## Codes d'erreur

| Code | Signification |
|---|---|
| `404` | plugin, manifeste ou extension introuvable |
| `400` | transition de publication invalide, validation échouée, permission non déclarée, plugin non publié, note d'avis hors `[1,5]` |

## Client Python officiel

```python
from tmis.platform_sdk.api_sdk.client import TmisApiClient
from tmis.platform_sdk.api_sdk.transports import HttpxTransport

client = TmisApiClient(HttpxTransport(base_url="https://cabinet.tmis.example.com"))
plugins = await client.list_marketplace_plugins(query="fiscal")
```

`TmisApiClient` ne dépend que de `HttpTransportPort`
(`async def request(method, path, json=None) -> dict`) — un client
dans un autre langage n'a qu'à implémenter ce même contrat contre les
mêmes routes REST documentées ci-dessus (voir
docs/65-architecture-platform-sdk.md, "ce que ce sprint ne fait pas").
