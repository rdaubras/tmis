# Rapport d'architecture — Sprint 27 (RAG et connecteurs branchés sur données réelles)

## Résumé

Le Sprint 27 ajoute des adaptateurs réels derrière les trois ports que
les Sprints 2 et 5 n'avaient implémentés qu'en mémoire/fixture :
`IndexPort` (`QdrantVectorIndex`), `EmbeddingProviderPort`
(`SentenceTransformerEmbeddingProvider`), et `ConnectorPort` (5
adaptateurs : `LegifranceConnector`, `JudilibreConnector`, et
`HttpConnector` réutilisé pour doctrine/internal_documentation/
private_database). Le prompt exigeait une Phase 0 de re-audit avant tout
code ; cet audit (docs/reports/sprint-27-rapport-audit.md) n'a trouvé
**aucun écart** avec ses prémisses — les 9 fichiers désignés avaient
exactement la forme attendue, donc aucun arbitrage utilisateur n'a été
nécessaire avant de commencer.

Périmètre livré : `backend/src/tmis/ai/rag/adapters/` (3 fichiers),
`backend/src/tmis/ai/embeddings/adapters/` (1 fichier) +
`ai/embeddings/factory.py`, `backend/src/tmis/ai/connectors/adapters/`
(4 fichiers) + `ai/connectors/factory.py`,
`legal_research/connectors/factory.py`,
`platform/health/connector_backend_check.py`, 12 settings ajoutés à
`core.config.Settings`, 48 tests dédiés.

## Décisions structurantes

### La bascule mémoire/réel vit dans des factories, jamais dans les ports ni leurs consommateurs

Aucune classe qui implémente un port ne connaît l'existence d'une autre
implémentation du même port ; aucune classe qui consomme un port
(`RagPipeline`, `HybridRetriever`, `DocumentEmbeddingBridge`,
`TMISKernel`, `ConnectorManager`) n'a de branche conditionnelle sur la
configuration. La décision vit exclusivement dans quatre fonctions de
composition (`tmis.ai.rag.factory.get_vector_index()`,
`tmis.ai.embeddings.factory.get_embedding_provider()`,
`tmis.ai.connectors.factory.build_*`,
`tmis.legal_research.connectors.factory.build_*`), appelées uniquement
depuis les deux points de bootstrap process-wide déjà existants
(`ai.kernel.bootstrap.get_kernel()`, `legal_research.bootstrap.
get_research_orchestrator()`). `hybrid_retriever.py` et
`document_intelligence/embeddings/bridge.py` — les deux consommateurs
d'`IndexPort` explicitement protégés par le prompt — n'ont reçu
**aucune** modification ; c'est vérifiable par `git diff` sur ces deux
fichiers.

### `ConnectorManager` et `register_legal_research_connectors` : extension additive, même patron que le Sprint 26

`ConnectorManager.__init__` gagne trois paramètres optionnels
(`codes`/`jurisprudence`/`doctrine`, défaut `None` → fixtures Sprint 2
inchangées) ; `register_legal_research_connectors()` gagne deux
paramètres optionnels (`internal_documentation`/`private_database`,
défaut `None` → fixtures Sprint 5 inchangées). C'est exactement le
patron que le Sprint 26 a utilisé pour `ReasoningOrchestrator
(session_store: SessionStorePort | None = None)` : un paramètre
optionnel remplace une construction interne codée en dur, sans qu'aucun
appelant existant sans argument ne change de comportement — vérifié par
`test_manager_with_no_args_still_defaults_to_the_sprint2_fixtures` et
`test_manager_lists_default_connectors` (préexistant, toujours vert).

### Un seul client Qdrant, un seul client HTTP connecteurs — jamais un par module

`tmis.ai.rag.adapters.qdrant_client_factory.get_qdrant_client()` est
`@lru_cache` : c'est le seul endroit du dépôt qui construit un
`AsyncQdrantClient`. De la même façon,
`tmis.ai.connectors.adapters.http_client_factory.
get_connector_http_client()` est le seul point de construction d'un
`httpx.AsyncClient` partagé par `LegifranceConnector`,
`JudilibreConnector` et chaque instance d'`HttpConnector`. Les deux
clients sont construits sans sonder leur backend (`check_compatibility
=False` côté Qdrant ; aucun appel réseau à la construction côté
`httpx.AsyncClient`) — une indisponibilité du service distant remonte au
premier appel réel, jamais à la construction du singleton, exactement
comme `RedisMemoryStore`/`RedisCache` (Sprint 2/10) ne pinguent pas
Redis à la construction.

### `QdrantVectorIndex` : id de point stable, upsert idempotent

`InMemoryVectorIndex.upsert()` ajoute toujours une entrée à sa liste
interne — un ré-upsert du même `chunk_id` crée un doublon logique
(l'ancienne entrée reste cherchable). `QdrantVectorIndex` dérive un id
de point Qdrant stable par `uuid5(NAMESPACE_URL, chunk_id)`, donc un
ré-upsert du même `chunk_id` écrase le point existant. Ce n'est **pas**
un changement de contrat d'`IndexPort` (le port ne spécifie aucune
sémantique d'idempotence), mais une divergence de comportement entre les
deux implémentations, documentée dans le docstring de
`QdrantVectorIndex` et couverte par un test dédié
(`test_upsert_is_idempotent_per_chunk_id`) plutôt que laissée
implicite.

### Embeddings : échec de chargement = repli, jamais un plantage

`get_embedding_provider()` enveloppe la construction de
`SentenceTransformerEmbeddingProvider` dans un `try/except Exception`
générique (paquet absent, réseau indisponible pour le téléchargement du
modèle, cache corrompu — toute cause) et retombe sur
`HashingEmbeddingProvider` en journalisant un avertissement. Ce n'est
pas seulement une règle du prompt appliquée mécaniquement : le
comportement s'est déclenché réellement pendant le développement, le
proxy sortant de cet environnement bloquant `huggingface.co`
(`403 Forbidden`) — voir la section Vérification finale.

### Connecteurs : source publique réelle nommée quand elle existe, HTTP générique sinon — jamais un mensonge silencieux

Le prompt distinguait explicitement « API publique pertinente si elle
existe » de « sinon un connecteur HTTP générique configurable ». Pour
codes/jurisprudence, une source publique réelle existe (Légifrance et
Judilibre, toutes deux via la passerelle PISTE de la DILA) : deux
adaptateurs nommés, partageant un `PisteOAuthTokenProvider` (jeton
OAuth2 mis en cache jusqu'à expiration). Pour doctrine — aucune API
publique pertinente pour la doctrine juridique française — et pour les
deux connecteurs du LRE — des sources par nature propres au cabinet, pas
publiques —, un seul `HttpConnector` générique configurable, réutilisé
trois fois plutôt que dupliqué. Dans les deux cas, l'absence de
configuration ne fait *jamais* passer silencieusement un appelant du
backend réel au backend fixture sans le dire : chaque factory journalise
un `connector.fixture_fallback` au premier appel, et
`ConnectorBackendHealthCheck` (nouveau, additif — voir plus bas) le
rapporte en continu via `/health`.

### Health check : DEGRADED plutôt que DOWN, additif au mécanisme existant

`ConnectorBackendHealthCheck` implémente `HealthCheckPort` directement
(pas via `CallableHealthCheck`, qui ne modélise que UP/DOWN) parce
qu'un connecteur sur sa fixture est fonctionnel — juste pas branché sur
des données réelles — et mérite `DEGRADED`, pas `DOWN`. Il est enregistré
dans `get_health_check_engine()` aux côtés des sept vérifications
existantes (base de données, cache, stockage, AI Kernel, event bus,
queue, connecteurs) sans toucher `HealthCheckEngine`/`HealthCheckPort`
eux-mêmes — même principe de composition que le reste du sprint.

## Périmètre volontairement réduit (documenté, pas construit)

Le prompt mentionnait, au conditionnel, un second fournisseur
d'embeddings à clé API optionnelle qui basculerait lui-même sur
`HashingEmbeddingProvider` en son absence. Aucun fournisseur concret
n'étant nommé, l'ajouter n'aurait été qu'une seconde variante du même
mécanisme de repli déjà implémenté pour le fournisseur local — sans
capacité nouvelle à démontrer, et avec le risque réel de fabriquer une
intégration à une API tierce non spécifiée. `get_embedding_provider()`
est écrit pour qu'une troisième branche s'ajoute en quelques lignes le
jour où un fournisseur concret est choisi (voir
docs/153-architecture-rag-production.md, section Embeddings).

## Reuse ledger

| Composant nouveau | Compose | Ne reconstruit jamais |
|---|---|---|
| `ai.rag.adapters.qdrant_index.QdrantVectorIndex` | `IndexPort` (Sprint 2, inchangé) | Un second contrat d'indexation |
| `ai.rag.adapters.qdrant_client_factory.get_qdrant_client` | `core.config.Settings.qdrant_url` (préexistant) | Un second client Qdrant par module |
| `ai.rag.factory.get_vector_index` | `InMemoryVectorIndex` (Sprint 2, conservé) | Une logique de sélection dans `RagPipeline`/`TMISKernel` |
| `ai.embeddings.adapters.sentence_transformer_provider.SentenceTransformerEmbeddingProvider` | `EmbeddingProviderPort` (Sprint 2, inchangé) | Un second contrat d'embedding |
| `ai.embeddings.factory.get_embedding_provider` | `HashingEmbeddingProvider` (Sprint 2, conservé) | Une logique de sélection dans `RagPipeline`/`TMISKernel` |
| `ai.connectors.adapters.legifrance_connector`/`judilibre_connector` | `ConnectorPort` (Sprint 2, inchangé), `PisteOAuthTokenProvider` | Un second contrat de connecteur |
| `ai.connectors.adapters.http_connector.HttpConnector` | `ConnectorPort` (Sprint 2, inchangé) | Trois classes quasi identiques pour doctrine/internal_documentation/private_database |
| `ai.connectors.adapters.http_client_factory.get_connector_http_client` | rien (nouveau besoin : un pool HTTP partagé) | Un client HTTP par connecteur |
| `ai.connectors.factory`, `legal_research.connectors.factory` | `ConnectorManager.register()`/paramètres optionnels (existant), fixtures Sprints 2/5 (conservées) | Un second registre de connecteurs |
| `platform.health.connector_backend_check.ConnectorBackendHealthCheck` | `HealthCheckPort`, `HealthCheckEngine.register()` (Sprint "supervision", inchangés) | Un second mécanisme de health check |

## Vérification finale

- `ruff check src tests` → All checks passed
- `mypy src` (strict, 1886 fichiers) → Success, aucune erreur
- `pytest` → 2057 tests passants, 5 skipped (2 déjà préexistants —
  Redis —, 3 nouveaux : téléchargement de modèle réel, gatés par
  `TMIS_RUN_MODEL_DOWNLOAD_TESTS`, même patron que
  `TMIS_REDIS_URL`)
- Vérification manuelle bout en bout : `get_kernel()` et
  `get_research_orchestrator()` sans aucune variable d'environnement
  positionnée → 5 connecteurs sur leur fixture Sprint 2/5, embedding
  `hashing-bow`, `/health` rapporte `connector_backends: degraded` avec
  le détail des 5 connecteurs ; positionner
  `TMIS_PISTE_CLIENT_ID`/`SECRET` fait basculer `codes`/`jurisprudence`
  sur `LegifranceConnector`/`JudilibreConnector` sans redémarrage de
  code.

## Corrections apportées pendant la vérification

- `AsyncQdrantClient(url=...)` sonde la compatibilité du serveur à la
  construction par défaut (`check_compatibility=True`), un appel réseau
  que rien d'autre dans ce dépôt ne fait à la construction d'un
  adaptateur — désactivé explicitement (`check_compatibility=False`)
  après l'avoir vu émettre un avertissement bruyant en tests.
- `mypy --strict` a rejeté `dict[str, object]` pour les payloads JSON
  parsés (`.get()` sur un `dict[str, object]` renvoie `object`, non
  itérable/indexable sans narrowing) — remplacé par `dict[str, Any]`,
  cohérent avec le seul autre endroit du dépôt qui parse une réponse
  HTTP JSON sous mypy strict (`platform_sdk.api_sdk.transports`).
- Une ligne de test asserait un chemin HTTP (`/search`) sans tenir
  compte du préfixe de chemin du `base_url` de test (`/api`) — corrigé
  dans le test, pas dans l'adaptateur (le comportement de l'adaptateur
  était correct).
- Téléchargement réel du modèle `sentence-transformers` impossible dans
  cet environnement (proxy sortant bloque `huggingface.co`, `403`) —
  confirme en conditions réelles que le repli de
  `get_embedding_provider()` fonctionne ; le test qui télécharge
  réellement le modèle est gaté par une variable d'opt-in
  (`TMIS_RUN_MODEL_DOWNLOAD_TESTS`), sur le même patron que les tests
  Redis existants (`TMIS_REDIS_URL`).
