# Rapport d'audit initial — Sprint 28 (Cache Redis en production + reranker appris)

Ce rapport précède toute implémentation, conformément à l'exigence
explicite du sprint (« Phase 0 — Re-audit avant code »). Il recense, par
lecture directe du code (jamais par déduction depuis les noms), ce qui
existe déjà pour les ports et implémentations concernés, et confirme
qu'aucun des neuf fichiers désignés par le prompt n'a changé de forme
depuis les Sprints 2/5/23 — comme au Sprint 27, cette Phase 0 n'a trouvé
**aucun écart** nécessitant un arbitrage utilisateur avant de commencer.

## Composants réutilisés tels quels

| Composant existant | Ce qu'il fournit déjà | Usage dans le Sprint 28 |
|---|---|---|
| `ai.cache.ports.CachePort` | `get`/`set`/`delete`/`exists`, tous `async def`, forme exacte confirmée par lecture | Implémenté par `RedisCache` et `InMemoryCache`, signature inchangée |
| `ai.cache.in_memory_cache.InMemoryCache` | Cache process-local sur `dict`, expiration par `time.monotonic()` | Conservé sans modification ; défaut si Redis ne répond pas au `PING` |
| `ai.cache.redis_cache.RedisCache` | Wrapper fin sur `redis.asyncio.Redis`, préfixage de clé, TTL | Conservé sans modification ; c'est la classe câblée réellement pour la première fois ce sprint — elle existait depuis le Sprint 2 mais n'était construite que par les tests d'intégration opt-in (`test_redis_backends.py`) |
| `ai.reranking.ports.RerankerPort` | `rerank(query, chunks) -> list[RetrievedChunk]`, `def` synchrone (pas `async`), forme exacte confirmée par lecture | Implémenté à l'identique par `CrossEncoderReranker` |
| `ai.reranking.simple_reranker.KeywordOverlapReranker` | Boost déterministe par correspondance de phrase exacte | Conservé sans modification (hormis le docstring, voir plus bas) ; défaut si `TMIS_RERANKER_BACKEND` n'est pas `cross_encoder` ou si le modèle échoue à charger |
| `legal_research.cache.research_cache.ResearchCache` | Trois couches de cache (brut/normalisé/classé), chacune sur `CachePort` | Conservé sans modification ; hérite du nouveau `RedisCache` via `kernel.cache` sans le savoir |
| `legal_research.cache.schemas.ResearchCacheConfig`, `RawSearchCacheEntry` | TTL par couche, forme de l'entrée brute | Conservés sans modification |
| `legal_research.bootstrap.get_research_orchestrator` | Compose déjà `ResearchCache(DistributedCacheEngine(kernel.cache))`, `@lru_cache` | **Zéro modification** — pas de câblage en dur à remplacer, contrairement à ce que le prompt supposait (voir « Écarts identifiés » plus bas) |
| `ai.retrieval.hybrid_retriever.HybridRetriever` | Combine score vectoriel (`IndexPort.search`) et recouvrement lexical, dépend uniquement des ports | **Zéro modification** — confirmé par lecture puis par `git diff` après implémentation ; ne consomme pas le reranker (voir « Écarts identifiés ») |
| `ai.connectors.factory`, `legal_research.connectors.factory` (Sprint 27) | Patron `build_*()` / `*_status()` : configuré + joignable/chargeable → adaptateur réel, sinon fixture, jamais un plantage | Patron reproduit pour `ai.cache.factory.make_cache()` et `ai.reranking.factory.get_reranker()`, jamais réinventé |
| `ai.kernel.kernel.TMISKernel.__init__` | Paramètre optionnel `cache: CachePort \| None = None`, défaut codé en dur `InMemoryCache()` | Défaut remplacé par `make_cache()` ; paramètre optionnel intact, aucun appelant qui injecte déjà un cache ne change de comportement |
| `platform_sdk.connector_sdk.base.BaseConnectorPlugin.__init__` | Paramètre optionnel `cache: CachePort \| None = None`, défaut codé en dur `InMemoryCache()` | Même remplacement, même garantie |
| `ai_fabric.bootstrap.get_response_cache` | `@lru_cache`, construit `ResponseCache(InMemoryCache())` codé en dur | Défaut remplacé par `ResponseCache(make_cache())` |
| `ai.kernel.bootstrap.get_kernel` | Singleton `@lru_cache` du `TMISKernel`, construit déjà `RagPipeline` avec l'embedding provider et l'index du Sprint 27 | Étendu (pas remplacé) : passe désormais aussi `reranker=get_reranker()` à `RagPipeline` |
| `ai.embeddings.adapters.sentence_transformer_provider.SentenceTransformerEmbeddingProvider` | Patron d'import différé (`from sentence_transformers import ...` à l'intérieur du constructeur) | Reproduit à l'identique par `CrossEncoderReranker` (import différé de `CrossEncoder`, même paquet `sentence-transformers`, aucune dépendance supplémentaire) |
| `ai.embeddings.factory.get_embedding_provider` | Patron de factory : flag `Settings`, `try/except Exception` générique autour du chargement du modèle, log + repli | Reproduit à l'identique par `ai.reranking.factory.get_reranker()` |
| `ai.rag.adapters.qdrant_client_factory.get_qdrant_client` | Patron de client singleton `@lru_cache`, un seul par dépôt | Reproduit par `ai.cache.factory._shared_redis_client()` pour le client `redis.asyncio.Redis` |
| `core.config.Settings` (préfixe `TMIS_`) | `redis_url` déjà présent (défaut `redis://localhost:6379/0`) ; seule source de configuration lue par tout le dépôt | Étendu de 2 nouveaux settings (`reranker_backend`, `cross_encoder_model_name`) — `redis_url` réutilisé tel quel, aucun nouveau setting de cache nécessaire |
| `tmis.core.tasks.celery_app` (Sprint 26) | Seul mécanisme Celery du dépôt, réutilise déjà `redis_url` comme broker/backend | Vérifié avant implémentation : gère son propre cycle de vie de connexion, indépendant de `CachePort` ; confirme qu'aucun second mécanisme de connexion Redis n'existait avant ce sprint |

## Composants étendus (changement additif, aucune rupture)

| Composant | Extension apportée | Pourquoi une extension et non un nouveau composant |
|---|---|---|
| `ai.kernel.kernel.TMISKernel.__init__` | `cache or make_cache()` remplace `cache or InMemoryCache()` | Le paramètre optionnel existait déjà (Sprint 2) ; seule sa valeur par défaut change — aucun appelant existant qui passe `cache=...` explicitement n'est affecté |
| `platform_sdk.connector_sdk.base.BaseConnectorPlugin.__init__` | `cache if cache is not None else make_cache()` remplace `... else InMemoryCache()` | Même raisonnement |
| `ai_fabric.bootstrap.get_response_cache` | `ResponseCache(make_cache())` remplace `ResponseCache(InMemoryCache())` | Même raisonnement — fonction déjà `@lru_cache`, aucune signature ne change |
| `ai.kernel.bootstrap.get_kernel` | Un appel `reranker=get_reranker()` de plus dans la construction de `RagPipeline` | `RagPipeline.__init__` a déjà un paramètre optionnel `reranker: RerankerPort \| None = None` (Sprint 2) ; aucun changement de signature |
| `ai.reranking.simple_reranker.KeywordOverlapReranker` (docstring uniquement) | La référence obsolète « planned for Sprint 9 » corrigée en Sprint 28, avec pointeur vers `CrossEncoderReranker` | Le prompt le demande explicitement ; aucun changement de comportement |
| `core.config.Settings` | 2 settings ajoutés (`reranker_backend`, `cross_encoder_model_name`) | Le reranker a besoin d'un flag pour savoir s'il doit s'activer, même mécanisme que `embedding_backend`/`rag_vector_index_backend` (Sprint 27) ; `redis_url` n'a besoin d'aucun flag supplémentaire (voir docs/155, section sélection par joignabilité) |

## Composants réellement nouveaux (aucun équivalent trouvé)

| Nouveau composant | Justification |
|---|---|
| `ai.cache.factory.make_cache` | Aucun point de composition ne décidait entre `InMemoryCache` et `RedisCache` — les trois appelants construisaient chacun `InMemoryCache()` en dur, `RedisCache` n'était construite que par les tests |
| `ai.cache.factory._shared_redis_client` | Aucun client `redis.asyncio.Redis` n'était construit nulle part dans `src/` (seuls les tests d'intégration en construisaient un, jetable, par test) |
| `ai.reranking.adapters.cross_encoder_reranker.CrossEncoderReranker` | Aucune implémentation apprise de `RerankerPort` n'existait — seule `KeywordOverlapReranker` |
| `ai.reranking.factory.get_reranker` | Aucune fonction ne décidait entre plusieurs `RerankerPort` — un seul existait |
| `docs/155-architecture-cache-production.md`, `docs/156-guide-reranker.md` | Aucun document ne couvrait le câblage cache réel ni le reranker appris |

## Écarts identifiés en Phase 0

Deux points de contexte, aucun ne bloquant (pas d'arbitrage utilisateur
nécessaire, contrairement au Sprint 26 qui en avait trouvé deux
bloquants) :

1. **`legal_research.bootstrap.get_research_orchestrator` n'a pas de
   câblage en dur à remplacer.** Le prompt le désigne comme « point
   d'injection du cache du LRE », ce qui est vrai, mais sa lecture
   montre qu'il compose déjà `ResearchCache(DistributedCacheEngine
   (kernel.cache))` depuis le Sprint 23 (migration documentée dans le
   rapport d'audit de ce sprint) — pas de `InMemoryCache()` codé en dur
   à ce niveau. Une fois `TMISKernel.cache` branché sur `make_cache()`,
   les trois couches du LRE héritent automatiquement du nouveau
   comportement sans qu'une seule ligne de `legal_research/bootstrap.py`
   ne change — vérifié par `git diff` sur ce fichier après
   implémentation (vide).

2. **`ai.retrieval.hybrid_retriever.HybridRetriever` ne consomme pas le
   reranker.** Le prompt le désigne comme « consommateur du reranker »,
   mais sa lecture montre qu'il ne dépend que d'`IndexPort` et
   d'`EmbeddingProviderPort` pour produire les candidats scorés — le
   reranking est une étape séparée et postérieure, appliquée par
   `ai.rag.pipeline.RagPipeline.query()`
   (`self._reranker.rerank(query, candidates)`) sur les candidats déjà
   retournés par le retriever. Les deux fichiers sont liés dans le
   pipeline (le retriever produit ce que le reranker consomme) mais ne
   sont pas le même point d'injection. Conséquence pratique : comme
   `hybrid_retriever.py` est aussi protégé de toute modification par le
   principe « aucun consommateur de port ne connaît la configuration »
   déjà établi au Sprint 27, ce point de contexte n'a changé aucune
   décision d'implémentation — `hybrid_retriever.py` n'a reçu, comme
   prévu, **aucune modification** (confirmé par `git diff`).

## Décisions de périmètre prises pendant l'implémentation (pas des écarts de prémisses, des choix d'ingénieur)

1. **`make_cache()` sonde Redis par un `PING` borné au démarrage,
   contrairement à la convention « jamais de sonde à la construction »
   établie au Sprint 27** (`get_qdrant_client(check_compatibility=
   False)`, `get_connector_http_client()`). Le prompt de ce sprint
   demande explicitement cette sémantique (« RedisCache si `redis_url`
   configuré et joignable ») ; voir docs/155-architecture-cache-
   production.md pour la justification complète (`CachePort` est sur le
   chemin chaud de pratiquement chaque appel du Kernel, contrairement à
   Qdrant/HTTP).

2. **Pas de nouveau setting pour sélectionner le backend de cache.**
   Contrairement au reranker (`TMIS_RERANKER_BACKEND`, même patron que
   `TMIS_EMBEDDING_BACKEND`), le cache ne lit que `redis_url` déjà
   existant — la sélection se fait par joignabilité, pas par flag
   explicite, parce que le prompt formule la règle ainsi (« si `redis_url`
   configuré et joignable ») et qu'`redis_url` a toujours une valeur par
   défaut (contrairement à `piste_client_id`/`doctrine_connector_base_url`,
   `None` par défaut) : un flag séparé aurait été redondant avec la
   variable déjà utilisée par Celery pour le même Redis.

3. **`make_cache()` n'est pas elle-même `@lru_cache`e ; seule la sonde/le
   client Redis sous-jacents le sont (`_shared_redis_client`).** Un
   `make_cache()` mise en cache aurait fait partager un unique
   `InMemoryCache` (un seul `dict`) entre `TMISKernel`, chaque
   `BaseConnectorPlugin`, et `ResponseCache` — une régression de
   comportement caractérisée par un test préexistant
   (`test_connector_search_uses_cache_on_second_call`), puisque deux
   connecteurs distincts partageant le même `plugin_id` dans des tests
   différents auraient alors partagé leurs entrées de cache. Voir
   docs/155, section « Un seul client Redis, jamais un par appelant »
   pour le détail de cette distinction (client Redis partagé,
   `InMemoryCache` jamais partagée).

## Conclusion

Le développement a pu commencer immédiatement après cette Phase 0 :
aucun écart de prémisses à trancher, deux points de contexte identifiés
et documentés sans bloquer (un fichier déjà branché sans changement
nécessaire, un fichier désigné par erreur comme consommateur direct du
reranker), et aucun nouveau composant proposé ne duplique une capacité
déjà présente dans le dépôt.
