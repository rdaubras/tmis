# Guide des Connecteurs (Sprint 13)

## Ce que `connector_sdk` fait pour vous

`tmis.platform_sdk.connector_sdk.BaseConnectorPlugin` implémente une
seule fois — pour tous les connecteurs — les cinq exigences du
sprint :

| Exigence | Implémentation |
|---|---|
| Authentification | `authenticate(context)` — hook optionnel, no-op par défaut |
| Pagination | `search()` boucle sur `fetch_page(query, page)` jusqu'à `max_pages` ou `has_next=False` |
| Gestion des erreurs | une exception dans `fetch_page` devient un avertissement, jamais un crash |
| Normalisation | `normalize(item)` — identité par défaut, à surcharger |
| Cache | `tmis.ai.cache.ports.CachePort` (Sprint 2), `InMemoryCache` par défaut |

## Ce qu'un auteur de connecteur implémente

Une seule méthode obligatoire :

```python
class ConnectorGedPlugin(BaseConnectorPlugin):
    def __init__(self) -> None:
        super().__init__(plugin_id="connector-ged")

    async def fetch_page(self, query: str, page: int) -> ConnectorPage:
        ...  # appel à la source réelle, une page à la fois
        return ConnectorPage(items=(...,), has_next=...)

    def normalize(self, item: dict) -> dict:
        return {"id": item["doc_id"], "title": item["titre"]}
```

`search()` — appelé automatiquement par `invoke()` — orchestre le
reste :

```python
result = await connector.search(context, "contrat de bail", max_pages=2)
result.items      # tuple normalisée
result.warnings   # une entrée par page en échec, jamais une exception propagée
```

## Cache

La clé de cache est `f"connector:{plugin_id}:{query}:{max_pages}"` et
la valeur est le JSON des éléments normalisés, avec un TTL de 5
minutes par défaut. Un second appel identique dans la fenêtre de TTL
ne rappelle jamais `fetch_page` — vérifié par un test dédié
(`test_connector_search_uses_cache_on_second_call`).

## Exemple complet

Voir `tmis.platform_sdk.examples.connector_ged` — un connecteur
fictif vers une gestion électronique de documents, avec pagination
réelle (deux éléments par page) et normalisation des champs.
