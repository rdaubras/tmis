# Référence API — Legal Integration Hub (Sprint 18)

Base : `/api/v1/integration-hub`. Documentation interactive complète
sur `/docs` (OpenAPI, généré automatiquement par FastAPI).

## Connecteurs

| Méthode | Chemin | Rôle |
|---|---|---|
| `GET` | `/connectors` | liste les connecteurs installés |
| `POST` | `/connectors/{connector_id}/disable` | désactive un connecteur |
| `POST` | `/connectors/{connector_id}/enable` | réactive un connecteur |
| `PUT` | `/connectors/{connector_id}/configuration` | définit la configuration (validée par `config_schema`) |
| `GET` | `/connectors/{connector_id}/configuration` | `?firm_id=...` — configuration active |

## Synchronisation

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/sync-jobs` | crée un job de synchronisation |
| `GET` | `/sync-jobs` | `?firm_id=...` — jobs du cabinet |
| `POST` | `/sync-jobs/{job_id}/run` | `?firm_id=...` — exécute le job (pull) |

## Webhooks

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/webhooks` | crée un abonnement (entrant ou sortant) |
| `POST` | `/webhooks/{subscription_id}/inbound` | livraison entrante signée HMAC |

## Supervision

| Méthode | Chemin | Rôle |
|---|---|---|
| `GET` | `/health` | état de santé agrégé, un composant par connecteur |

## Codes d'erreur

| Code | Signification |
|---|---|
| `404` | connecteur, job de synchronisation, abonnement ou configuration introuvable |
| `422` | valeur de configuration manquante, direction ou mode invalide (validation Pydantic) |

## Exemple

```python
import httpx

client = httpx.Client(base_url="https://cabinet.tmis.example.com/api/v1/integration-hub")

client.put(
    "/connectors/crm-demo/configuration",
    json={"firm_id": "firm-123", "values": {"api_key": "xxx"}},
)
job = client.post(
    "/sync-jobs",
    json={"firm_id": "firm-123", "connector_id": "crm-demo", "entity_type": "client"},
).json()
report = client.post(f"/sync-jobs/{job['id']}/run", params={"firm_id": "firm-123"}).json()
print(report["records_written"], report["conflicts"])
```
