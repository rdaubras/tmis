# Référence API — Autonomous Legal Workflow Platform (Sprint 17)

Base : `/api/v1/workflow-automation`. Documentation interactive
complète sur `/docs` (OpenAPI, généré automatiquement par FastAPI).

## Workflows

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/workflows` | crée un workflow (version 1, statut `draft`) |
| `POST` | `/workflows/{workflow_id}/versions` | crée une nouvelle version |
| `POST` | `/workflows/{workflow_id}/activate` | active une version (archive l'ancienne active) |
| `POST` | `/workflows/{workflow_id}/archive` | archive une version |
| `GET` | `/workflows/{workflow_id}` | `?firm_id=...` — une version |
| `GET` | `/workflows/key/{workflow_key}/versions` | `?firm_id=...` — tout l'historique de versions |

## Modèles

| Méthode | Chemin | Rôle |
|---|---|---|
| `GET` | `/templates` | `?case_type=...` — modèles disponibles |
| `POST` | `/templates/{template_id}/instantiate` | crée un workflow réel à partir d'un modèle |

## Règles

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/rules` | crée une règle (comparateur simple) |
| `GET` | `/rules` | `?firm_id=&active_only=` — règles du cabinet |
| `POST` | `/rules/{rule_id}/deactivate` | désactive une règle |
| `POST` | `/rules/{rule_id}/evaluate` | évalue une règle contre un contexte |

## Exécution

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/executions/start` | lance une exécution |
| `POST` | `/executions/{execution_id}/resume` | reprend une exécution échouée/en pause |
| `GET` | `/executions/{execution_id}` | `?firm_id=...` — état complet |

## Simulation

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/simulate` | dry-run sur données fictives, jamais d'effet réel |

## Validation des actions critiques

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/approvals/configure` | configure si un type d'action requiert validation |
| `GET` | `/approvals/requires` | `?firm_id=&action_type=` — politique active |
| `POST` | `/approvals/request` | demande une validation |
| `POST` | `/approvals/{request_id}/decide` | approuver / rejeter / demander une révision |

## Audit

| Méthode | Chemin | Rôle |
|---|---|---|
| `GET` | `/audit` | `?firm_id=...` — journal complet |
| `GET` | `/audit/export` | `?firm_id=...` — export CSV téléchargeable |

## Codes d'erreur

| Code | Signification |
|---|---|
| `404` | workflow, exécution, règle ou demande d'approbation introuvable |
| `422` | comparateur ou décision invalide (validation Pydantic) |

## Exemple

```python
import httpx

response = httpx.post(
    "https://cabinet.tmis.example.com/api/v1/workflow-automation/executions/start",
    json={"firm_id": "firm-123", "workflow_id": "wf-abc123", "context": {"case_id": "dossier-1"}},
)
execution = response.json()
print(execution["status"], execution["step_results"])
```
