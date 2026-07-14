# Rapport d'audit initial — Sprint 27 (RAG et connecteurs branchés sur données réelles)

Ce rapport précède toute implémentation, conformément à l'exigence
explicite du sprint (« Phase 0 — Re-audit avant code »). Il recense, par
lecture directe du code (jamais par déduction depuis les noms), ce qui
existe déjà pour les ports et implémentations concernés, et confirme
qu'aucun des neuf fichiers désignés par le prompt n'a changé de forme
depuis les Sprints 2/5 — contrairement au Sprint 26, cette Phase 0 n'a
trouvé **aucun écart** nécessitant un arbitrage utilisateur avant de
commencer.

## Composants réutilisés tels quels

| Composant existant | Ce qu'il fournit déjà | Usage dans le Sprint 27 |
|---|---|---|
| `ai.rag.ports.IndexPort` | `upsert(chunks, vectors)` / `search(vector, *, top_k, filters)`, tous deux `async def`, forme exacte confirmée par lecture | Implémenté par `QdrantVectorIndex`, signature inchangée |
| `ai.rag.indexing.InMemoryVectorIndex` | Recherche cosinus brute-force, filtrage par métadonnées | Conservé sans modification ; défaut si `TMIS_RAG_VECTOR_INDEX_BACKEND` n'est pas `qdrant` |
| `ai.embeddings.ports.EmbeddingProviderPort` | `embedding_name: str`, `dimensions: int`, `async def embed(texts) -> list[list[float]]` | Implémenté par `SentenceTransformerEmbeddingProvider`, signature inchangée |
| `ai.embeddings.hashing_provider.HashingEmbeddingProvider` | Embedding bag-of-words déterministe, sans dépendance | Conservé sans modification ; défaut si `TMIS_EMBEDDING_BACKEND` n'est pas `sentence_transformers` |
| `ai.connectors.ports.ConnectorPort` | `connector_name: str`, `async def search(query, filters)`, `async def fetch(document_id)` | Implémenté à l'identique par les 5 nouveaux adaptateurs |
| `ai.connectors.manager.ConnectorManager` | `register`/`enable`/`disable`/`is_enabled`/`list_connectors`/`search`/`fetch`, isolation des pannes par `ConnectorError` | Seul registre utilisé ; aucun second registre créé |
| `ai.connectors.codes_connector.CodesConnector`, `jurisprudence_connector.JurisprudenceConnector`, `doctrine_connector.DoctrineConnector` | 3 fixtures en mémoire (Sprint 2) | Conservés sans modification ; défaut si aucune configuration externe n'est fournie |
| `legal_research.connectors.registration.register_legal_research_connectors` | Enregistre 2 connecteurs sur le `ConnectorManager` du Kernel | Étendu de façon additive (voir plus bas), jamais remplacé |
| `legal_research.connectors.internal_documentation_connector.InternalDocumentationConnector`, `private_database_connector.PrivateDatabaseConnector` | 2 fixtures en mémoire (Sprint 5) | Conservés sans modification ; défaut si aucune configuration externe n'est fournie |
| `ai.retrieval.hybrid_retriever.HybridRetriever` | Combine score vectoriel (`IndexPort.search`) et recouvrement lexical, dépend uniquement des ports | **Zéro modification** — confirmé par lecture puis par `git diff` après implémentation |
| `document_intelligence.embeddings.bridge.DocumentEmbeddingBridge` | `embed_and_index`/`search`, défauts `HashingEmbeddingProvider()`/`InMemoryVectorIndex()` codés en dur | **Zéro modification** — reste le point d'entrée non branché sur les nouveaux adaptateurs (limite assumée, voir plus bas) |
| `ai.kernel.bootstrap.get_kernel` | Singleton `@lru_cache` du `TMISKernel`, seul point de construction process-wide | Étendu (pas remplacé) : construit désormais l'embedding provider, l'index et les 3 connecteurs Sprint 2 via les nouvelles factories avant de les injecter dans `TMISKernel`/`RagPipeline` |
| `legal_research.bootstrap.get_research_orchestrator` | Singleton `@lru_cache`, appelle `register_legal_research_connectors(kernel.connector_manager)` | Étendu : passe désormais les 2 connecteurs LRE construits via `legal_research.connectors.factory` |
| `platform.health.bootstrap.get_health_check_engine` | 7 vérifications `CallableHealthCheck` enregistrées | Étendu d'une 8ᵉ vérification (`ConnectorBackendHealthCheck`), même mécanisme `HealthCheckEngine.register()` |
| `core.config.Settings` (préfixe `TMIS_`) | `qdrant_url` déjà présent ; seule source de configuration lue par tout le dépôt | Étendu de 12 nouveaux settings (voir rapport d'architecture) — aucune seconde config créée |

## Composants étendus (changement additif, aucune rupture)

| Composant | Extension apportée | Pourquoi une extension et non un nouveau composant |
|---|---|---|
| `ai.connectors.manager.ConnectorManager.__init__` | 3 paramètres optionnels `codes`/`jurisprudence`/`doctrine: ConnectorPort \| None = None` | Remplace la construction interne codée en dur (`CodesConnector()` etc.) à l'identique quand aucun argument n'est passé — même patron que `ReasoningOrchestrator(session_store=...)` au Sprint 26 ; `ConnectorManager()` sans argument continue de donner exactement les 3 fixtures Sprint 2 (test de non-régression dédié) |
| `legal_research.connectors.registration.register_legal_research_connectors` | 2 paramètres optionnels `internal_documentation`/`private_database: ConnectorPort \| None = None` | Même raisonnement ; `register_legal_research_connectors(manager)` sans ces arguments continue de donner exactement les 2 fixtures Sprint 5 |
| `platform.health.bootstrap.get_health_check_engine` | Un appel `engine.register(ConnectorBackendHealthCheck())` de plus | Le sprint a besoin qu'un connecteur en mode fixture soit visible ailleurs qu'en log de démarrage ; l'engine existant le permet déjà sans modification de `HealthCheckEngine`/`HealthCheckPort` |
| `core.config.Settings` | 12 settings ajoutés (Qdrant, embeddings, PISTE, HTTP générique — voir docs/154) | Chaque adaptateur réel a besoin d'au moins une variable pour savoir s'il doit s'activer ; tous passent par le même mécanisme que `qdrant_url`/`database_url`/`redis_url` déjà en place |
| `backend/pyproject.toml` | `qdrant-client` en dépendance de production ; `sentence-transformers` en dépendance de dev **et** en extra optionnel dédié (`rag-local`) | `qdrant-client` est demandé explicitement par le prompt et reste léger (pas de dépendance `torch`) ; `sentence-transformers` entraîne `torch` (~500 Mo) — extra séparé pour qu'une installation de base (`pip install tmis`) n'hérite pas de ce poids si le backend réel n'est pas utilisé, conformément à « le mode dev sans dépendances doit continuer à fonctionner tel quel » |

## Composants réellement nouveaux (aucun équivalent trouvé)

| Nouveau composant | Justification |
|---|---|
| `ai.rag.adapters.qdrant_index.QdrantVectorIndex` | Aucune implémentation réelle d'`IndexPort` n'existait — seule `InMemoryVectorIndex` |
| `ai.rag.adapters.qdrant_client_factory.get_qdrant_client` | Aucun client Qdrant n'était construit nulle part dans le dépôt |
| `ai.rag.factory.get_vector_index` | Aucun point de composition ne choisissait entre plusieurs `IndexPort` — un seul existait |
| `ai.embeddings.adapters.sentence_transformer_provider.SentenceTransformerEmbeddingProvider` | Aucune implémentation réelle d'`EmbeddingProviderPort` n'existait — seule `HashingEmbeddingProvider` |
| `ai.embeddings.factory.get_embedding_provider` | Même raison que `get_vector_index` |
| `ai.connectors.adapters.piste_oauth.PisteOAuthTokenProvider` | Aucun flux OAuth2 client-credentials n'existait dans le dépôt |
| `ai.connectors.adapters.legifrance_connector.LegifranceConnector`, `judilibre_connector.JudilibreConnector` | Aucun appel HTTP réel vers une source juridique externe n'existait — les 5 connecteurs Sprint 2/5 sont tous des fixtures en mémoire |
| `ai.connectors.adapters.http_connector.HttpConnector` | Aucun connecteur HTTP générique configurable n'existait |
| `ai.connectors.adapters.http_client_factory.get_connector_http_client` | Aucun client HTTP partagé pour les connecteurs n'existait |
| `ai.connectors.factory`, `legal_research.connectors.factory` | Aucune fonction ne décidait entre fixture et adaptateur réel — cette décision n'existait pas avant ce sprint |
| `platform.health.connector_backend_check.ConnectorBackendHealthCheck` | Aucune vérification de santé par connecteur n'existait (`_check_connectors` existant ne vérifie que la présence du `ConnectorManager`, pas ce qu'il contient) |
| `docs/153-architecture-rag-production.md`, `docs/154-guide-configuration-connecteurs.md` | Aucun document ne couvrait la bascule mémoire/réel pour ces ports |

## Écarts identifiés en Phase 0

Aucun. Les neuf fichiers désignés par le prompt (`ai/rag/ports.py` et
`indexing.py` ; `ai/embeddings/ports.py` et `hashing_provider.py` ;
`ai/connectors/ports.py`, `manager.py`, `codes_connector.py`,
`jurisprudence_connector.py`, `doctrine_connector.py` ;
`legal_research/connectors/registration.py`,
`internal_documentation_connector.py`, `private_database_connector.py` ;
`hybrid_retriever.py` ; `document_intelligence/embeddings/bridge.py` ;
`core/config.py`) ont été lus intégralement avant tout code et
correspondaient exactement à la description du prompt : mêmes
signatures, mêmes comportements par défaut, `qdrant_url` déjà présent
dans `Settings`. Aucun arbitrage utilisateur n'a donc été nécessaire
avant de commencer — à la différence du Sprint 26, qui en avait trouvé
deux (une `Base` SQLAlchemy préexistante, un port de stockage manquant).

## Décisions de périmètre prises pendant l'implémentation (pas des écarts de prémisses, des choix d'ingénieur)

Ces points n'ont pas nécessité d'arrêt ni d'arbitrage utilisateur — ce
sont des choix dans l'espace explicitement laissé ouvert par le prompt
(« API publique pertinente si elle existe... sinon un connecteur HTTP
générique » ; « tests d'intégration... via testcontainers ou
équivalent ») — mais ils sont documentés ici par transparence :

1. **Pas de second fournisseur d'embeddings à clé API.** Le prompt
   mentionnait cette option au conditionnel, sans nommer de fournisseur
   concret. L'ajouter aurait été une seconde variante du même mécanisme
   de repli déjà implémenté pour `SentenceTransformerEmbeddingProvider`
   (`get_embedding_provider()` capture déjà toute exception et retombe
   sur `HashingEmbeddingProvider`), sans capacité nouvelle. Voir
   docs/153, section Embeddings.

2. **Pas de testcontainers pour Qdrant.** Confirmé par recherche dans
   `backend/tests` : aucun test de ce dépôt n'utilise testcontainers
   (le pattern déjà en place pour "un moteur réel sans service externe à
   déployer" est `aiosqlite`, utilisé par les 7 tests d'intégration
   SQLAlchemy du Sprint 26). Docker n'est de toute façon pas disponible
   dans cet environnement (`docker ps` échoue : pas de daemon). L'
   intégration Qdrant est donc testée via le mode local intégré de
   `qdrant-client` (`AsyncQdrantClient(location=":memory:")`) — le même
   moteur que celui utilisé en production, embarqué plutôt que joint par
   le réseau, l'équivalent le plus proche du choix `aiosqlite` déjà
   établi dans ce dépôt pour la même contrainte.

3. **Endpoints Légifrance/Judilibre non validés contre le service réel.**
   Aucun identifiant PISTE n'est disponible dans cet environnement, et
   le proxy sortant du bac à sable bloque de toute façon les hôtes non
   allowlistés (vérifié : une tentative de téléchargement de modèle vers
   `huggingface.co` a été rejetée avec `403 Forbidden`). Les chemins
   d'endpoint et formes de requête/réponse suivent la documentation
   publique de la passerelle PISTE ; chaque champ lu dans la réponse est
   traité défensivement (`.get(...)` avec repli) et les URLs de base
   restent configurables, pour qu'une dérive de schéma côté DILA se
   corrige en configuration. Les tests couvrent le contrat HTTP via
   `httpx.MockTransport`, pas un appel réel.

4. **`document_intelligence.embeddings.bridge.DocumentEmbeddingBridge`
   n'est pas branché sur les nouvelles factories.** Le prompt protégeait
   explicitement ce fichier de toute modification (« ne doivent
   nécessiter aucun changement »). Son constructeur garde donc ses
   défauts `HashingEmbeddingProvider()`/`InMemoryVectorIndex()` codés en
   dur — un appelant qui veut le backend réel doit les lui passer
   explicitement. C'est cohérent avec la limite acceptée du Sprint 26
   (`case_intelligence.bootstrap.get_case_intelligence_workflow()` non
   reciblé sur `SQLAlchemyCaseStore`) : étendre le câblage par défaut
   d'un point de composition qui n'est pas un des deux bootstraps
   process-wide du sprint est hors périmètre, documenté plutôt que fait
   silencieusement.

## Conclusion

Le développement a pu commencer immédiatement après cette Phase 0 :
aucun écart de prémisses à trancher, une seule extension additive
identifiée par composant (paramètres optionnels sur `ConnectorManager`
et `register_legal_research_connectors`, une vérification de plus sur
`HealthCheckEngine`), et aucun nouveau composant proposé ne duplique une
capacité déjà présente dans le dépôt.

## Correctifs post-clôture

**Signalement reçu :** l'extra optionnel `rag-local` (et l'extra `dev`,
qui inclut aussi `sentence-transformers`) tirerait transitivement numpy
2.5.1, dont les stubs utilisent la syntaxe PEP 695 — incompatible avec
`[tool.mypy] python_version = "3.11"` — ce qui casserait `mypy src` sur
tout le dépôt.

**Vérification effectuée :**

1. Runtime réel confirmé 3.11 partout : `backend/Dockerfile`
   (`FROM python:3.11-slim`), `.github/workflows/ci.yml`
   (`python-version: "3.11"`), `pyproject.toml` `[project]`
   (`requires-python = ">=3.11"`). Le runtime cible n'est donc pas
   `>=3.12` — relever `[tool.mypy] python_version` à `3.12` ne
   s'appliquerait pas ici ; ce serait désynchroniser mypy du runtime
   réel, pas une correction.
2. Reproduction en environnement isolé, à l'identique de l'étape CI
   (`python3.11 -m venv` puis `pip install -e ".[dev]"`) : pip résout
   **numpy 2.4.6**, jamais 2.5.1. `pip download numpy==2.5.1` confirme
   que cette version (et 2.5.0, qui introduit la syntaxe PEP 695 dans
   ses stubs) déclare `Requires-Python >=3.12` — numpy a abandonné le
   support 3.11 exactement à la version qui casse mypy en mode 3.11.
   Le résolveur pip ne peut donc mécaniquement jamais sélectionner une
   version cassante tant que ce dépôt cible 3.11 : c'est déjà garanti
   par les métadonnées du paquet numpy lui-même, sans borne de version
   supplémentaire côté `pyproject.toml`.
3. `mypy src` exécuté sur cette installation reproductible (numpy
   2.4.6, sentence-transformers 5.6.0, mypy 1.20.2) :
   `Success: no issues found in 1886 source files` — aucune erreur, y
   compris en mode `strict`.

**Décision :** aucun changement de code. Le risque décrit est réel et
documenté dans l'écosystème mypy/numpy (voir
[python/mypy#18701](https://github.com/python/mypy/issues/18701)), mais
il ne se matérialise pas dans ce dépôt tant que le runtime reste 3.11,
parce que numpy verrouille lui-même la compatibilité via
`Requires-Python`. Ajouter un pin `numpy<2.5` serait une contrainte
redondante, sans effet observable, pour un scénario que pip exclut déjà
mécaniquement — donc non ajoutée.

**Point de vigilance (pas une action requise maintenant) :** si le
runtime (Dockerfile + CI + `requires-python`) est un jour porté à
Python `>=3.12`, `[tool.mypy] python_version` (et `target-version`
ruff) devront être relevés dans le même commit — c'est à ce moment-là,
et seulement à ce moment-là, que numpy 2.5.x devient installable et que
sa syntaxe PEP 695 imposera cet alignement.
