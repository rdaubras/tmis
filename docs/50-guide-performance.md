# Guide Performance (Sprint 10)

## Périmètre

`tmis.platform.performance`, `tmis.platform.cache`,
`tmis.platform.cost_control`.

## Pagination

`PageRequest` (page 1-indexée, `page_size` borné à 200 via
`__post_init__`, qui utilise `object.__setattr__` car la dataclass est
`frozen`). `paginate()` découpe une séquence déjà matérialisée et
triée — la référence pour un store en mémoire ; un store adossé à une
vraie base de données doit pousser `LIMIT`/`OFFSET` en SQL plutôt que
d'appeler `paginate()` sur une liste entièrement chargée, mais les
formes `Page`/`PageRequest` restent identiques dans les deux cas.

## Cache

`CachePolicyRegistry` (`platform/cache/policy.py`) **n'est pas** une
réimplémentation du cache : c'est une couche de politique de TTL par
type de ressource, au-dessus de `tmis.ai.cache.CachePort` (Sprint 2).
Elle centralise ce qui était sinon un magic number dispersé à chaque
site d'appel.

## Parallélisation des workflows IA

`bounded_gather(coroutines, max_concurrency)` exécute un ensemble de
coroutines concurremment, jamais plus de `max_concurrency` à la fois
(`asyncio.Semaphore`) — utile partout où TMIS lance plusieurs appels
`TMISKernel.complete()` en parallèle (ex. rédiger plusieurs sections
indépendantes) sans dépasser la capacité d'un fournisseur de modèle à
débit limité.

## Benchmarks

`benchmark(name, fn, iterations)` mesure moyenne/p95/min/max sur un
chemin chaud (requête, sérialisation, lookup de cache) — un outil de
micro-benchmark pour un test ou un script ponctuel, pas un substitut à
un outil de test de charge réel contre un déploiement en fonctionnement.

## Suivi des coûts IA

`CostTrackerEngine` réutilise directement
`tmis.ai.evaluation.metrics.estimate_cost` (le même modèle de coût que
`TMISKernel` utilise pour `EvaluationMetrics.estimated_cost_usd`), donc
les chiffres de coût ne divergent jamais entre les deux. Mesures :
coût par utilisateur/dossier/workflow/fournisseur, taux de succès du
cache (`cache_hit_rate`), seuils d'alerte configurables par périmètre
(`firm`/`user`) sur une fenêtre glissante (`check_thresholds`).

**Limite connue** : `TMISKernel.complete()` ne propage pas encore de
contexte utilisateur/dossier/workflow — rien n'appelle `record()`
automatiquement aujourd'hui. Un appelant doit explicitement rapporter
le coût après avoir enveloppé un appel au Kernel. Cette limite est la
même que celle déjà documentée pour
`tmis.cabinet_os.analytics.AIUsagePort` (Sprint 9).

## Tests de charge

Voir `tests/integration/platform/test_platform_load_integration.py` :
50 identités × 20 requêtes concurrentes à travers `InMemoryRateLimiter`
(chacune plafonnée exactement à sa limite configurée, sans fuite entre
identités), verrouillage `BruteForceProtector` sous échecs concurrents,
et un test de volume (10 000 vérifications sur 100 identités doit rester
rapide — garde-fou contre une régression en O(n) d'un lookup censé être
O(1)).
