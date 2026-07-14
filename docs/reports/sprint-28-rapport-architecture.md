# Rapport d'architecture — Sprint 28 (Cache Redis en production + reranker appris)

## Résumé

Le Sprint 28 est un sprint de câblage, pas de construction : `CachePort`,
`RedisCache`, `InMemoryCache`, `ResearchCache` et `RerankerPort`
existaient tous déjà (Sprint 2) et fonctionnaient, mais trois points de
composition (`TMISKernel`, `BaseConnectorPlugin`,
`ai_fabric.bootstrap.get_response_cache`) construisaient `InMemoryCache()`
en dur, et `RagPipeline` ne recevait jamais que `KeywordOverlapReranker`.
La Phase 0 de re-audit (docs/reports/sprint-28-rapport-audit.md) a
confirmé que les neuf fichiers désignés par le prompt avaient exactement
la forme attendue — deux points de contexte identifiés (un fichier déjà
branché, un fichier désigné par erreur comme consommateur direct du
reranker), aucun bloquant.

Périmètre livré : `ai/cache/factory.py` (nouveau),
`ai/reranking/adapters/cross_encoder_reranker.py` (nouveau),
`ai/reranking/factory.py` (nouveau), trois câblages en dur remplacés
(`ai/kernel/kernel.py`, `platform_sdk/connector_sdk/base.py`,
`ai_fabric/bootstrap.py`), `ai/kernel/bootstrap.py` étendu (reranker
injecté dans `RagPipeline`), 2 settings ajoutés à `core.config.Settings`,
20 tests dédiés.

## Décisions structurantes

### La bascule mémoire/réel vit dans des factories, jamais dans les ports ni leurs consommateurs

Même principe qu'au Sprint 27 : aucune classe qui implémente `CachePort`
ou `RerankerPort` ne connaît l'existence de l'autre implémentation ;
aucune classe qui les consomme (`TMISKernel`, `BaseConnectorPlugin`,
`ResponseCache`, `ResearchCache`, `RagPipeline`) n'a de branche
conditionnelle sur la configuration. La décision vit exclusivement dans
deux fonctions de composition (`ai.cache.factory.make_cache()`,
`ai.reranking.factory.get_reranker()`), appelées depuis les trois points
de bootstrap déjà existants qui construisaient un défaut en dur
(`TMISKernel.__init__`, `BaseConnectorPlugin.__init__`,
`ai_fabric.bootstrap.get_response_cache`) plus, pour le reranker, le
point de composition process-wide `ai.kernel.bootstrap.get_kernel()`.

### `make_cache()` sélectionne par joignabilité, pas par flag — écart assumé à la convention du Sprint 27

Les factories du Sprint 27 décident sur un flag `Settings` explicite
(`TMIS_RAG_VECTOR_INDEX_BACKEND`, `TMIS_EMBEDDING_BACKEND`) et ne sondent
jamais le backend à la construction (`get_qdrant_client
(check_compatibility=False)`, aucun appel réseau dans
`get_connector_http_client()`) : l'indisponibilité remonte au premier
appel réel, jamais à la construction du singleton.

`make_cache()` s'écarte délibérément de cette convention : elle sonde
Redis par un `PING` synchrone borné (`socket_connect_timeout=0.5s`) au
moment de la construction, mise en cache une fois par process
(`_shared_redis_client`, `@lru_cache`). Deux raisons, documentées en
détail dans docs/155-architecture-cache-production.md :

1. Le prompt du sprint spécifie explicitement cette sémantique
   (« RedisCache si `redis_url` configuré **et joignable**, sinon
   InMemoryCache »), contrairement aux prompts RAG/connecteurs du
   Sprint 27 qui ne demandaient qu'un flag.
2. `CachePort` est sur le chemin chaud de pratiquement chaque appel du
   Kernel (`complete()`, `search_connectors()`), de chaque connecteur, et
   des trois couches du cache du LRE — contrairement à Qdrant (utilisé
   seulement quand le RAG est réellement invoqué) ou aux connecteurs
   HTTP (déjà enveloppés d'un `try/except` qui transforme une panne en
   avertissement, voir `BaseConnectorPlugin.search()`). Différer la
   détection au premier appel réel aurait propagé une `ConnectionError`
   non gérée à chacun de ces points d'appel dès que Redis devient
   indisponible en cours de vie du process — un échec bien plus
   disruptif que le coût borné (0,5 s, une seule fois par process) d'un
   `PING` au démarrage.

### `make_cache()` elle-même n'est pas mise en cache — seul le client Redis sous-jacent l'est

Distinction délibérée entre deux niveaux de cache dans
`ai.cache.factory` :

- `_shared_redis_client()` est `@lru_cache` : au plus un `PING`, au plus
  un client `redis.asyncio.Redis` construit par process, quel que soit
  le nombre d'appelants — c'est le mécanisme de connexion Redis unique
  exigé par le prompt.
- `make_cache()` ne l'est **pas** : chaque appel retourne soit une
  nouvelle `RedisCache` légère (partageant le client/pool ci-dessus),
  soit une nouvelle `InMemoryCache` (un `dict` privé, jamais partagé).

Cette seconde moitié de la distinction reproduit exactement le
comportement préexistant de la branche mémoire : avant ce sprint, chaque
appelant (`TMISKernel()`, chaque `BaseConnectorPlugin`, `ResponseCache`)
construisait son propre `InMemoryCache()` privé. Un `make_cache()`
entièrement mis en cache aurait fait fuir des entrées entre connecteurs
distincts partageant le même `plugin_id` dans des instances différentes
— un scénario réel couvert par un test préexistant
(`test_connector_search_uses_cache_on_second_call`), qui aurait
commencé à échouer de façon intermittente selon l'ordre d'exécution des
tests si la mémorisation avait été appliquée sans discrimination. Voir
`test_make_cache_returns_a_fresh_in_memory_instance_each_call` et
`test_all_redis_cache_instances_share_the_one_client`
(`tests/unit/ai/test_cache_factory.py`) pour la couverture des deux
moitiés de cette garantie.

### `CrossEncoderReranker` : même patron d'import différé et de repli que `SentenceTransformerEmbeddingProvider`, aucune dépendance nouvelle

`CrossEncoderReranker.__init__` importe `sentence_transformers.
CrossEncoder` à l'intérieur du constructeur (pas au niveau module),
exactement comme `SentenceTransformerEmbeddingProvider` importe
`SentenceTransformer` — le paquet `sentence-transformers` (extra
optionnel `rag-local` depuis le Sprint 27) fournit les deux classes,
aucune dépendance supplémentaire à `pyproject.toml`. `ai.reranking.
factory.get_reranker()` enveloppe la construction dans un `try/except
Exception` générique et retombe sur `KeywordOverlapReranker` en
journalisant un avertissement — même structure exacte que `ai.embeddings.
factory.get_embedding_provider()`. Ce repli s'est déclenché en conditions
réelles pendant le développement de ce sprint : le proxy sortant de
l'environnement de développement bloque `huggingface.co` (`403
Forbidden`, la même contrainte déjà rencontrée au Sprint 27 pour le
modèle d'embedding) — confirmant que le repli fonctionne sous une
véritable panne réseau, pas seulement sous un mock.

### `RerankerPort.rerank()` est synchrone — `CrossEncoderReranker` ne fait donc aucun `asyncio.to_thread`

`RerankerPort.rerank(query, chunks) -> list[RetrievedChunk]` est un
`def`, pas un `async def` (confirmé en Phase 0, contrairement à
`EmbeddingProviderPort.embed()` qui est `async`). `CrossEncoderReranker.
rerank()` appelle donc `self._model.predict(pairs)` directement, sans le
`asyncio.to_thread` que `SentenceTransformerEmbeddingProvider.embed()`
utilise pour ne pas bloquer la boucle d'événements — la différence de
signature du port impose la différence d'implémentation, ce n'est pas
une incohérence entre les deux adaptateurs.

## Périmètre volontairement réduit (documenté, pas construit)

Aucun health check dédié n'a été ajouté pour le reranker ou le cache
(contrairement à `ConnectorBackendHealthCheck` au Sprint 27). Un
connecteur sur sa fixture est un signal utile pour un opérateur (source
de données non branchée), mais un cache qui retombe sur `InMemoryCache`
ou un reranker qui retombe sur `KeywordOverlapReranker` restent
pleinement fonctionnels — juste moins performants à l'échelle ou moins
précis — et sont déjà journalisés au démarrage
(`cache.redis_unreachable`/`cache.backend_selected`,
`reranker.cross_encoder_unavailable`/`reranker.backend_selected`), sur le
même principe que documenté dans docs/156, section « Vérifier ce qui est
réellement actif ». Ajouter un health check dédié n'aurait démontré
aucune capacité nouvelle par rapport au patron déjà établi
(`ConnectorBackendHealthCheck` existe déjà pour le cas où un signal
`/health` explicite est réellement nécessaire).

## Reuse ledger

| Composant nouveau | Compose | Ne reconstruit jamais |
|---|---|---|
| `ai.cache.factory.make_cache` | `CachePort` (Sprint 2, inchangé), `InMemoryCache`/`RedisCache` (Sprint 2, conservées) | Une logique de sélection dans `TMISKernel`/`BaseConnectorPlugin`/`ResponseCache` |
| `ai.cache.factory._shared_redis_client` | `core.config.Settings.redis_url` (préexistant, déjà utilisé par Celery) | Un second client Redis par module ; un second mécanisme de connexion Redis (vérifié contre `tmis.core.tasks.celery_app` en Phase 0) |
| `ai.reranking.adapters.cross_encoder_reranker.CrossEncoderReranker` | `RerankerPort` (Sprint 2, inchangé), paquet `sentence-transformers` (déjà dépendance depuis le Sprint 27) | Un second contrat de reranking |
| `ai.reranking.factory.get_reranker` | `KeywordOverlapReranker` (Sprint 2, conservé) | Une logique de sélection dans `RagPipeline`/`TMISKernel` |

## Vérification finale

- `ruff check src tests` → All checks passed
- `mypy src` (strict, 1890 fichiers) → Success, aucune erreur
- `pytest` → 2075 tests passants, 7 skipped (3 Redis — 2 préexistants, 1
  nouveau —, 4 téléchargement de modèle réel — 3 préexistants, 1
  nouveau —, tous gatés par `TMIS_REDIS_URL`/
  `TMIS_RUN_MODEL_DOWNLOAD_TESTS`, même patron que le Sprint 27)
- Couverture globale : 95,75 % (seuil CI 90 %) ; `ai/cache/factory.py`,
  `ai/reranking/factory.py`, `ai/reranking/adapters/
  cross_encoder_reranker.py` : 100 %
- Vérification manuelle bout en bout, aucune variable d'environnement
  positionnée : `get_kernel().cache` → `InMemoryCache`, journalise
  `cache.redis_unreachable` (`Error 111 connecting to localhost:6379.
  Connection refused`, aucune exception propagée) ; `get_kernel().rag.
  _reranker` → `KeywordOverlapReranker` ; `get_response_cache()._backend`
  → `InMemoryCache` ; `get_research_orchestrator()` construit sans
  erreur. Positionner `TMIS_RERANKER_BACKEND=cross_encoder` déclenche
  bien une tentative de chargement réelle du modèle
  (`cross-encoder/ms-marco-MiniLM-L-6-v2`), qui échoue sur le proxy
  sortant du bac à sable (`403 Forbidden`) et retombe sur
  `KeywordOverlapReranker` en journalisant `reranker.
  cross_encoder_unavailable` — comportement vérifié en conditions
  réelles, pas seulement mocké.

## Corrections apportées pendant la vérification

- `redis.asyncio.Redis.from_url` n'a pas d'annotation de type de retour
  exploitable par `mypy --strict` (`Returning Any from function declared
  to return "Redis | None"`) — le paquet `redis` déclare `py.typed` mais
  cette méthode particulière reste sous-typée. Un `# type: ignore
  [no-any-return]` ciblé sur le seul appel concerné (`ai/cache/
  factory.py`), même patron que `# type: ignore[untyped-decorator]` déjà
  utilisé dans ce dépôt pour le décorateur Celery
  (`core/tasks/case_tasks.py`, `document_tasks.py`) — aucune suppression
  d'erreur plus large que nécessaire.
