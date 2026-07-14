# 154 — Guide : configurer les adaptateurs RAG et connecteurs réels

Toute la configuration du Sprint 27 passe par `tmis.core.config.Settings`
(préfixe d'environnement `TMIS_`) — le seul mécanisme de configuration du
dépôt, déjà utilisé par la base de données, Redis et Qdrant (`qdrant_url`
existait déjà). Aucune variable de ce sprint n'a de seconde source de
vérité (pas de second fichier `.env`, pas de config ad hoc dans un
module). Voir `docs/153-architecture-rag-production.md` pour
l'architecture ; ce guide ne couvre que les valeurs à positionner.

**Comportement par défaut (aucune variable ci-dessous positionnée)** :
tout reste en mémoire/fixture, exactement comme avant ce sprint —
`InMemoryVectorIndex`, `HashingEmbeddingProvider`, et les 5 connecteurs
fixture des Sprints 2/5. C'est le mode dev/tests, sans dépendance
externe.

## Index vectoriel (Qdrant)

| Variable | Défaut | Effet |
|---|---|---|
| `TMIS_RAG_VECTOR_INDEX_BACKEND` | `memory` | `qdrant` active `QdrantVectorIndex` |
| `TMIS_QDRANT_URL` | `http://localhost:6333` | déjà existant (Sprint "socle infra"), réutilisé tel quel |
| `TMIS_QDRANT_API_KEY` | *(vide)* | pour un déploiement Qdrant Cloud/protégé |
| `TMIS_QDRANT_COLLECTION` | `tmis_rag_chunks` | nom de la collection (une seule, filtrage par payload — voir docs/03) |
| `TMIS_QDRANT_TIMEOUT_SECONDS` | `10.0` | timeout client |

```bash
TMIS_RAG_VECTOR_INDEX_BACKEND=qdrant
TMIS_QDRANT_URL=http://qdrant.internal:6333
```

## Embeddings (modèle local)

| Variable | Défaut | Effet |
|---|---|---|
| `TMIS_EMBEDDING_BACKEND` | `hashing` | `sentence_transformers` active `SentenceTransformerEmbeddingProvider` |
| `TMIS_SENTENCE_TRANSFORMER_MODEL_NAME` | `paraphrase-multilingual-MiniLM-L12-v2` | tout modèle `sentence-transformers` compatible (téléchargé au premier usage) |

```bash
TMIS_EMBEDDING_BACKEND=sentence_transformers
```

Le paquet `sentence-transformers` est optionnel
(`pip install tmis[rag-local]`, ou déjà présent via les dépendances de
dev) : s'il est absent, ou si le téléchargement du modèle échoue, le
Kernel journalise un avertissement et continue avec
`HashingEmbeddingProvider` — aucun redémarrage cassé.

## Connecteurs — codes et jurisprudence (Légifrance / Judilibre, via PISTE)

Obtenez un identifiant PISTE sur [piste.gouv.fr](https://piste.gouv.fr/)
(inscription DILA), avec accès aux API Légifrance et Judilibre.

| Variable | Défaut | Effet |
|---|---|---|
| `TMIS_PISTE_CLIENT_ID` | *(vide)* | identifiant OAuth2 PISTE |
| `TMIS_PISTE_CLIENT_SECRET` | *(vide)* | secret OAuth2 PISTE |
| `TMIS_PISTE_OAUTH_TOKEN_URL` | `https://oauth.piste.gouv.fr/api/oauth/token` | rarement à changer |
| `TMIS_LEGIFRANCE_API_BASE_URL` | `https://api.piste.gouv.fr/dila/legifrance/lf-engine-app` | surchargeable si DILA change un chemin |
| `TMIS_JUDILIBRE_API_BASE_URL` | `https://api.piste.gouv.fr/cassation/judilibre` | idem |

Les deux connecteurs (`codes`, `jurisprudence`) basculent ensemble : les
identifiants PISTE sont communs aux deux API.

```bash
TMIS_PISTE_CLIENT_ID=xxxxxxxx
TMIS_PISTE_CLIENT_SECRET=xxxxxxxx
```

## Connecteurs — doctrine, documentation interne, base privée (HTTP générique)

Chacun des trois connecteurs suivants est indépendant : configurer l'un
n'affecte pas les autres. Chacun attend une API JSON exposant
`GET {base_url}/search?q=...` (réponse `{"results": [...]}` ou une liste
JSON brute) et `GET {base_url}/documents/{id}`, chaque document ayant au
minimum `id`, `title`, `content`, et optionnellement `metadata`.

| Connecteur | Variable base URL | Variable clé API (optionnelle) |
|---|---|---|
| doctrine | `TMIS_DOCTRINE_CONNECTOR_BASE_URL` | `TMIS_DOCTRINE_CONNECTOR_API_KEY` |
| internal_documentation | `TMIS_INTERNAL_DOCUMENTATION_CONNECTOR_BASE_URL` | `TMIS_INTERNAL_DOCUMENTATION_CONNECTOR_API_KEY` |
| private_database | `TMIS_PRIVATE_DATABASE_CONNECTOR_BASE_URL` | `TMIS_PRIVATE_DATABASE_CONNECTOR_API_KEY` |

```bash
TMIS_INTERNAL_DOCUMENTATION_CONNECTOR_BASE_URL=https://search.cabinet.example/api
TMIS_INTERNAL_DOCUMENTATION_CONNECTOR_API_KEY=xxxxxxxx
```

Si l'API du cabinet n'expose pas exactement ces deux chemins, ajustez
`search_path`/`document_path` en code au point d'appel de `HttpConnector`
(`tmis.legal_research.connectors.factory`,
`tmis.ai.connectors.factory`) — ce sont des paramètres du constructeur,
pas des variables d'environnement, pour rester au plus près des ports
existants sans faire grossir `Settings` avec des cas trop spécifiques à
un seul déploiement.

## Vérifier ce qui est réellement actif

- **Logs de démarrage** : chaque connecteur qui reste sur sa fixture
  journalise un `connector.fixture_fallback` avec la raison exacte.
- **`GET /health`** (readiness) : le composant `connector_backends`
  rapporte `degraded` avec le détail de chaque connecteur en mode
  fixture, `up` si les cinq sont sur leur backend réel.
- **`kernel.embedding_provider.embedding_name`** / **`kernel.rag`** :
  `"hashing-bow"` en mode par défaut,
  `"sentence-transformers:<model>"` en mode réel.
