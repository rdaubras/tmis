# Guide — Cache distribué étendu (Sprint 23)

## Le cache distribué existait déjà

L'audit a confirmé que `ai.cache.CachePort` (Sprint 2) est déjà une
abstraction de cache distribué réelle : `RedisCache` en est
l'implémentation de production, adossée au service `redis` de
`docker-compose.yml`. Ce sprint **étend** ce cache — il n'en crée pas
un second.

## Ce que `DistributedCacheEngine` ajoute

`runtime_platform.distributed_cache.DistributedCacheEngine` décore
n'importe quel `CachePort` (mémoire ou Redis) :

```python
cache = DistributedCacheEngine(redis_cache_or_in_memory)
await cache.set("k", "v", ttl_seconds=60)
value = await cache.get("k")
```

- **Invalidation** : `invalidate(key)` supprime la clé *et* notifie
  tout listener enregistré via `register_invalidation_listener` — un
  cache applicatif local (comme les trois couches de
  `legal_research.cache.ResearchCache`) peut ainsi savoir qu'une
  valeur a changé au-delà de ce que le stockage partagé Redis
  garantit déjà entre processus.
- **Cache warming** : `warm(loaders, ttl_seconds=...)` pré-remplit un
  ensemble de clés en ignorant celles déjà présentes.
- **Cache intelligent** : `_smart_ttl` est une heuristique — pas du
  machine learning — qui prolonge le TTL (jusqu'à x4) d'une clé
  accédée fréquemment, plutôt que de la laisser expirer au même
  rythme qu'une clé jamais relue.
- **Compression** : les valeurs de plus de 256 caractères sont
  compressées (zlib + base64) avant stockage si cela réduit
  effectivement leur taille ; `stats.bytes_saved_by_compression`
  historise le gain cumulé.
- **Statistiques d'usage** : `hits`, `misses`, `sets`,
  `invalidations`, `warmed_keys`, `bytes_saved_by_compression` — rien
  de tout cela n'était suivi par `CachePort` lui-même ni par
  `cloud_operations.cache.CacheObservabilityEngine` (qui ne fait
  qu'agréger ce que l'appelant lui rapporte manuellement).

## Migration représentative : `legal_research`

```mermaid
graph LR
    Kernel[TMISKernel.cache : CachePort] --> DCE[DistributedCacheEngine]
    DCE --> RC[legal_research.cache.ResearchCache]
```

`legal_research.bootstrap.get_research_orchestrator()` construit
désormais `ResearchCache(DistributedCacheEngine(kernel.cache))` au
lieu de `ResearchCache(kernel.cache)` directement — un changement
d'une ligne, à coût nul : `ResearchCache` n'appelle que `get`/`set`
sur son cache, deux méthodes que `DistributedCacheEngine` implémente
avec une signature identique à `CachePort`. Aucune API publique de
`ResearchCache` ni de `legal_research` n'a changé.
