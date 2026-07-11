# Référence API — AI Intelligence Fabric (Sprint 14)

Base : `/api/v1/ai-fabric`. Documentation interactive complète sur
`/docs` (OpenAPI, généré automatiquement par FastAPI).

## Modèles & fournisseurs

| Méthode | Chemin | Rôle |
|---|---|---|
| `GET` | `/models` | catalogue complet des `ModelDescriptor` |
| `GET` | `/models/{model_name}` | détail d'un modèle |
| `GET` | `/providers` | noms des fournisseurs enregistrés dans `ProviderRegistry` |

## Routage & planification

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/route` | sélectionne un modèle pour une tâche (retourne `reasons` explicables) |
| `POST` | `/plan` | décompose une tâche selon le pipeline par défaut du sprint |

## Évaluation & synthèse multi-modèles

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/compare` | classe plusieurs réponses au même prompt |
| `POST` | `/critique` | évalue une réponse (cohérence, citations, contradictions) — ne génère rien |
| `POST` | `/consensus` | synthèse argumentée entre plusieurs positions, divergences préservées |
| `POST` | `/fuse` | assemble plusieurs réponses en préservant citations et provenance |

## Benchmark

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/benchmark` | enregistre une mesure et met à jour `quality_score` du modèle |
| `GET` | `/benchmark` | dernier run de chaque modèle, trié par qualité |
| `GET` | `/benchmark/{model_name}` | historique complet des runs d'un modèle |

## Observabilité

| Méthode | Chemin | Rôle |
|---|---|---|
| `GET` | `/telemetry` | `?firm_id=...` — coût, qualité, disponibilité, taux d'usage, taux de fallback par modèle |
| `GET` | `/costs` | `?firm_id=...` — coût par fournisseur et taux de cache |

## Gouvernance & politiques

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/policies` | crée une politique (`model_forbidden`, `enterprise_only`, `country_restricted`, `data_type_restricted`) |
| `GET` | `/policies` | liste toutes les politiques |
| `POST` | `/policies/{policy_id}/deactivate` | désactive une politique |
| `POST` | `/governance/evaluate` | évalue les politiques actives pour un `(firm_id, modèle, pays, type)` |
| `GET` | `/governance/history` | `?firm_id=&model_name=` — historique des décisions passées |

## Codes d'erreur

| Code | Signification |
|---|---|
| `404` | modèle, politique ou ressource introuvable |
| `400` | aucun modèle éligible (`NoEligibleModelError`) |
| `429` | quota du cabinet dépassé (`QuotaExceededError`) |

## Exemple

```python
import httpx

response = httpx.post(
    "https://cabinet.tmis.example.com/api/v1/ai-fabric/route",
    json={
        "firm_id": "firm-123",
        "task_type": "Rédaction",
        "prompt": "Rédige un avis sur ce bail.",
        "profile": "drafting",
        "min_quality_score": 0.7,
    },
)
decision = response.json()
print(decision["model"]["name"], decision["reasons"])
```
