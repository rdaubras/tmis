# Référence API — Knowledge Graph Federation & Semantic Intelligence (Sprint 25)

Base : `/api/v1/knowledge-graph`. Documentation interactive complète sur
`/docs` (OpenAPI, généré automatiquement par FastAPI).

## Fédération cross-scope

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/federation/cross-scope` | `{"firm_id", "occurrences": [["case_graph"\|"document_knowledge_graph"\|"cabinet_ontology", node_id], ...]}` — un `FederatedNeighborhood` par occurrence connue |

## Résolution d'entités

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/entity-resolution/resolve` | résout un ensemble d'occurrences ; sous le seuil de confiance, route vers la validation humaine |
| `POST` | `/entity-resolution/{entity_id}/decide` | `{"firm_id", "approver_id", "decision": "approve"\|"reject"\|"request_revision"}` |
| `GET` | `/entity-resolution/{entity_id}` | `?firm_id=...` — l'entité résolue |
| `GET` | `/entity-resolution` | `?firm_id=...` — toutes les entités résolues du cabinet |

## Intelligence sémantique

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/semantic-intelligence/link` | `{"objects": [[id, texte], ...], "similarity_threshold"?}` — calcule et persiste les `SemanticLink` au-dessus du seuil |
| `GET` | `/semantic-intelligence/{object_id}` | tous les liens sémantiques touchant cet id |

## Analytics

| Méthode | Chemin | Rôle |
|---|---|---|
| `GET` | `/analytics/{firm_id}/snapshot` | moyennes historisées de `GRAPH_COVERAGE`, `ENTITY_RESOLUTION_RATE`, `SEMANTIC_LINK_DENSITY` |

## Gouvernance

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/governance/restrict-entity-visibility` | crée une `GovernancePolicy(type=RESTRICTED_ENTITY_VISIBILITY)` pour une entité résolue |
| `POST` | `/governance/evaluate-entity-visibility` | évalue si un rôle donné peut voir une entité restreinte |

## Pont Copilot (Knowledge Packs)

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/copilot-bridge/{pack_id}/attach-entities` | `{"firm_id", "entity_ids"}` — n'ajoute que les ids qui résolvent réellement |
| `POST` | `/copilot-bridge/{pack_id}/attach-relations` | `{"firm_id", "occurrences"}` — ajoute des refs de relations fédérées |
| `GET` | `/copilot-bridge/{pack_id}/relations` | `?firm_id=...` — résout les relations fédérées référencées par le pack |

## Codes d'erreur

| Code | Signification |
|---|---|
| `404` | entité résolue introuvable (`GET`/`decide` sur un id inconnu) |
| `422` | corps de requête invalide (validation Pydantic) |

## Exemple

```python
import httpx

response = httpx.post(
    "https://cabinet.tmis.example.com/api/v1/knowledge-graph/entity-resolution/resolve",
    json={
        "firm_id": "firm-123",
        "requested_by": "user-1",
        "occurrences": [
            {"origin": "case_graph", "node_id": "actor-1", "label": "Jean Dupont"},
            {"origin": "document_knowledge_graph", "node_id": "entity-42", "label": "Jean Dupont"},
        ],
    },
)
resolved = response.json()
print(resolved["status"], resolved["confidence"])
```
