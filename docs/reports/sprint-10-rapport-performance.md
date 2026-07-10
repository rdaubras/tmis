# Rapport de performance — Sprint 10 (Enterprise Platform)

## Mesures livrées

- **Pagination bornée** (`performance.pagination`) : `page_size` toujours
  plafonné à 200, empêchant un appelant de forcer une requête non bornée.
- **Politique de cache par type de ressource** (`cache.policy`) : TTL
  centralisé (`kernel_completion`, `research_raw`,
  `research_normalized`, `research_ranked`...) au-dessus de
  `tmis.ai.cache.CachePort` — plus de magic number dispersé par site
  d'appel.
- **Parallélisation bornée** (`performance.concurrency.bounded_gather`) :
  exécution concurrente plafonnée par `asyncio.Semaphore`, pour paralléliser
  des appels `TMISKernel.complete()` sans dépasser la capacité d'un
  fournisseur à débit limité.
- **Benchmarks** (`performance.benchmark`) : moyenne/p95/min/max sur un
  chemin chaud — outil de micro-benchmark, pas un substitut à un test de
  charge réel.
- **Suivi des coûts IA** (`cost_control`) : coût par utilisateur/dossier/
  workflow/fournisseur, taux de succès du cache, seuils d'alerte
  configurables par périmètre et fenêtre glissante. Réutilise
  `tmis.ai.evaluation.metrics.estimate_cost` — jamais de divergence de
  chiffre entre le Kernel et le suivi de coût.

## Tests de charge

`tests/integration/platform/test_platform_load_integration.py` :

- 50 identités × 20 requêtes concurrentes à travers
  `InMemoryRateLimiter` — chaque identité plafonnée exactement à sa
  limite configurée, aucune fuite entre identités sous concurrence
  réelle (`bounded_gather`, pas une boucle séquentielle).
- Verrouillage `BruteForceProtector` sous 5 échecs concurrents sur la
  même identité.
- Test de volume : 10 000 vérifications de limite de débit réparties
  sur 100 identités en moins de 2 secondes — garde-fou contre une
  régression accidentelle en O(n) d'un lookup censé rester O(1)
  (dictionnaire indexé par identité).

## Bug de performance/exactitude détecté et corrigé

**`Histogram.observe()`** (métriques Prometheus) incrémentait
initialement *tous* les buckets qualifiants à chaque observation, alors
que `render()` effectuait *aussi* une somme cumulative au moment du
rendu — un double comptage systématique (une observation à 0,3s sur des
buckets `[0.1, 1.0, 10.0]` remontait un compte de 2 sur le bucket
`le="1.0"` pour une seule observation, et pire pour les buckets
suivants). Corrigé en n'incrémentant que le premier bucket qualifiant
(`break` explicite) ; `render()` reste l'unique source de la sémantique
cumulative standard de Prometheus. Couvert par un test de non-régression
explicite (`test_histogram_bucket_counts_are_not_double_counted`).

## Limites connues

- `TMISKernel.complete()` ne propage pas encore de contexte utilisateur/
  dossier/workflow : `CostTrackerEngine.record()` ne peut donc pas être
  appelé automatiquement — même limite que celle déjà documentée pour
  `tmis.cabinet_os.analytics.AIUsagePort` (Sprint 9).
- Aucun test de charge contre un déploiement Kubernetes réel n'a été
  mené (les tests de charge de ce sprint exercent les moteurs en
  mémoire, pas l'infrastructure) — prévu au Sprint 27 "Performance &
  scalabilité" de la roadmap révisée.
