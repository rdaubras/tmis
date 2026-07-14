# 156 — Guide : reranker appris (Sprint 28)

Toute la configuration du Sprint 28 passe par `tmis.core.config.Settings`
(préfixe d'environnement `TMIS_`) — le seul mécanisme de configuration du
dépôt, déjà utilisé pour `TMIS_EMBEDDING_BACKEND`/
`TMIS_RAG_VECTOR_INDEX_BACKEND` au Sprint 27. Voir
`docs/155-architecture-cache-production.md` pour le cache Redis ; ce guide
ne couvre que le reranker.

**Comportement par défaut (aucune variable ci-dessous positionnée)** :
`KeywordOverlapReranker` (Sprint 2, recouvrement lexical exact) reste le
comportement de `RagPipeline`, exactement comme avant ce sprint — mode
dev/tests, sans dépendance externe, sans téléchargement de modèle.

## Activer le cross-encoder appris

| Variable | Défaut | Effet |
|---|---|---|
| `TMIS_RERANKER_BACKEND` | `keyword_overlap` | `cross_encoder` active `CrossEncoderReranker` |
| `TMIS_CROSS_ENCODER_MODEL_NAME` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | tout modèle cross-encoder `sentence-transformers` compatible (téléchargé au premier usage) |

```bash
TMIS_RERANKER_BACKEND=cross_encoder
```

Le paquet `sentence-transformers` est optionnel
(`pip install tmis[rag-local]`, ou déjà présent via les dépendances de
dev — même paquet que `SentenceTransformerEmbeddingProvider`, Sprint 27,
aucune dépendance supplémentaire) : s'il est absent, ou si le
téléchargement du modèle échoue, `ai.reranking.factory.get_reranker()`
journalise un avertissement (`reranker.cross_encoder_unavailable`) et
continue avec `KeywordOverlapReranker` — aucun redémarrage cassé. Ce
comportement a été vérifié en conditions réelles dans l'environnement de
développement de ce sprint : le proxy sortant bloque `huggingface.co`
(`403 Forbidden`), et le repli s'est déclenché exactement comme prévu.

## Ce que fait `CrossEncoderReranker`

Contrairement à `KeywordOverlapReranker`, qui ne regarde que le
recouvrement lexical entre la requête et chaque passage indépendamment,
un cross-encoder évalue la paire `(requête, passage)` conjointement à
travers un modèle transformer — un score par paire, pas une similarité
entre deux vecteurs précalculés (à la différence d'un bi-encoder comme
`SentenceTransformerEmbeddingProvider`, utilisé lui pour la recherche
initiale, pas le reranking). C'est plus coûteux par paire (un passage
`top_k * candidate_pool_multiplier` de `HybridRetriever` reste petit,
quelques dizaines de passages), mais généralement plus précis pour
classer un petit nombre de candidats déjà retrouvés — c'est pourquoi un
cross-encoder sert toujours en second étage (rerank), jamais en
recherche initiale sur tout un corpus.

`CrossEncoderReranker.rerank()` remplace le `score` de chaque
`RetrievedChunk` par le score du modèle et retrie par score décroissant
— même contrat que `KeywordOverlapReranker.rerank()`, aucun changement de
`RerankerPort`.

## Vérifier ce qui est réellement actif

- **Logs de démarrage** : `reranker.cross_encoder_unavailable` si le
  modèle n'a pas pu être chargé ; `reranker.backend_selected`
  (`backend=cross_encoder`) sinon.
- Aucun health check dédié n'a été ajouté (contrairement aux connecteurs,
  Sprint 27) : un reranker qui retombe sur `KeywordOverlapReranker` reste
  pleinement fonctionnel — juste moins précis — et le log de démarrage
  suffit à le diagnostiquer, sur le même principe que le cache (voir
  docs/155, qui journalise plutôt que d'exposer un composant `/health`
  dédié pour la même raison : un repli fonctionnel, pas une panne).
