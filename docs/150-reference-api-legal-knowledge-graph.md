# Référence API — Legal Knowledge Graph & Semantic Intelligence Platform (Sprint 25)

Base : `/api/v1/legal-knowledge-graph`. Documentation interactive
complète sur `/docs` (OpenAPI, généré automatiquement par FastAPI).
Chaque endpoint appelle `identity_platform.api.guard.authorize_or_403`
avec `Permission.KNOWLEDGE_GRAPH_MANAGE` — un appel sans autorisation
suffisante reçoit `403`.

## Ingestion & publication (Phase 5)

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/ingest` | `{firm_id, user_id, source_type, title, content_text, author, source_refs?}` — Import → Extraction → Classification → Enrichissement → Validation |
| `POST` | `/publish` | `{firm_id, user_id, knowledge_object_id, approver}` — publication, distincte de la validation |
| `POST` | `/validation/{request_id}/decide` | `{firm_id, user_id, decision, reviewer, comment?}` — `decision` ∈ `approve`/`reject`/`request_changes` |

## Recherche sémantique (Phase 3)

| Méthode | Chemin | Rôle |
|---|---|---|
| `GET` | `/search` | `?firm_id=&user_id=&query=&top_k=` — recherche par intention, classée par score |

## Nœuds & relations (Phase 2)

| Méthode | Chemin | Rôle |
|---|---|---|
| `GET` | `/nodes/{node_id}/relations` | `?firm_id=&user_id=` — relations explicables (source/target/type/explanation/confidence) ; liste vide si le nœud n'a aucune relation |
| `GET` | `/nodes/{node_id}/neighbors` | `?firm_id=&user_id=` — nœuds voisins ; `404` si `node_id` n'existe pas |

## Boucle de validation humaine (Phase 6)

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/feedback` | `{firm_id, user_id, subject_id, action, author, comment?}` — `action` ∈ `accept`/`modify`/`reject`/`annotate`/`explain` |

## Résolution d'entités (Phase 4)

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/entity-resolution/propose` | `{firm_id, user_id, node_id_a, node_id_b}` — score + auto-confirmation si nom normalisé identique |
| `POST` | `/entity-resolution/{match_id}/confirm` | `{firm_id, user_id, actor}` — confirmation humaine, crée une relation `SAME_AS` |
| `POST` | `/entity-resolution/{match_id}/reject` | `{firm_id, user_id, actor}` — rejet humain, aucune relation créée |

## Gouvernance (Phase 8)

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/nodes/{node_id}/policy` | `{firm_id, user_id, confidentiality_level?, retention_days?}` — métadonnées seulement, la décision d'accès reste dans `identity_platform` |

## Qualité (Phase 9)

| Méthode | Chemin | Rôle |
|---|---|---|
| `GET` | `/nodes/{node_id}/quality` | `?firm_id=&user_id=` — score de confiance (doublons, incohérences, sources manquantes) ; `404` si le nœud n'existe pas |

## Analytics (Phase 10)

| Méthode | Chemin | Rôle |
|---|---|---|
| `GET` | `/analytics` | `?firm_id=&user_id=` — taille du graphe, latence de recherche, qualité moyenne, validations humaines, enrichissements |

## Voir aussi

- docs/145-architecture-legal-knowledge-graph.md
- docs/85-reference-api-ai-governance.md — même convention `authorize_or_403`
