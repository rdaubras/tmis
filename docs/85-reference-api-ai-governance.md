# Référence API — AI Governance & Explainability Platform (Sprint 15)

Base : `/api/v1/ai-governance`. Documentation interactive complète sur
`/docs` (OpenAPI, généré automatiquement par FastAPI).

## Reasoning Chain

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/chain/steps` | `?firm_id=&production_id=` — enregistre une étape (stage/summary/references) |
| `GET` | `/chain/{production_id}` | `?firm_id=...` — chaîne complète |
| `GET` | `/chain/{production_id}/graph` | `?firm_id=...` — vue graphe (nodes/edges) |

## Decision Records

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/decisions` | enregistre une décision (contexte, objectif, alternatives, justification) |
| `GET` | `/decisions/{production_id}` | `?firm_id=...` — historique complet |

## Confidence & Risk

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/confidence` | calcule un score décomposé en 5 facteurs |
| `POST` | `/risks` | évalue les risques et les classe par gravité |

## Explainability & Provenance

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/explanations` | génère un rapport d'explicabilité |
| `GET` | `/explanations/{production_id}` | `?firm_id=...` — historique des rapports |
| `POST` | `/provenance` | associe un élément à sa source (4 granularités) |
| `GET` | `/provenance/{production_id}` | `?firm_id=...` — trace de provenance complète |

## Traceability & Lineage

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/trace` | enregistre un élément tracé (kind/reference/detail) |
| `GET` | `/trace/{production_id}` | `?firm_id=...` — chaîne de traçabilité |
| `POST` | `/lineage` | enregistre l'origine (et la révision éventuelle) d'une production |
| `GET` | `/lineage/{production_id}` | `?firm_id=...` — chaîne de révision complète |

## Détection (biais, hallucination, éthique)

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/bias-scan` | `{"text": "..."}` — détecteurs extensibles |
| `POST` | `/hallucination-scan` | `{"text": "..."}` — alertes + recommandations, jamais de suppression |
| `POST` | `/ethics-scan` | `{"text": "..."}` — dépistage déontologique, avis consultatif |

## Politiques de gouvernance

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/policies` | crée une politique (5 types, configurable par cabinet) |
| `GET` | `/policies` | `?firm_id=...` — politiques actives |
| `POST` | `/policies/{policy_id}/deactivate` | désactive une politique |
| `POST` | `/policies/evaluate` | évalue une production contre les politiques actives |

## Validation humaine

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/validations/simple` | un seul approbateur suffit |
| `POST` | `/validations/multiple` | tous les approbateurs doivent valider |
| `POST` | `/validations/hierarchical` | niveaux ordonnés (`approver_tiers`) |
| `POST` | `/validations/{request_id}/decide` | approuver / rejeter / demander une révision |
| `GET` | `/validations/{production_id}` | `?firm_id=...` — historique des demandes |

## Audit IA

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/audit` | enregistre une entrée d'audit IA |
| `GET` | `/audit` | `?firm_id=...` — toutes les entrées du cabinet |
| `GET` | `/audit/export` | `?firm_id=...` — export CSV téléchargeable |

## Conformité & Qualité

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/compliance/check` | évalue politiques + risques et rend un verdict |
| `POST` | `/quality` | calcule le score global de gouvernance (5 facteurs) |

## Vue d'ensemble

| Méthode | Chemin | Rôle |
|---|---|---|
| `GET` | `/overview/{production_id}` | `?firm_id=...` — toutes les informations consultables en une lecture |

## Codes d'erreur

| Code | Signification |
|---|---|
| `404` | demande de validation introuvable |
| `422` | corps de requête invalide (validation Pydantic) |

## Exemple

```python
import httpx

response = httpx.post(
    "https://cabinet.tmis.example.com/api/v1/ai-governance/compliance/check",
    json={
        "firm_id": "firm-123",
        "production_id": "prod-1",
        "is_export": True,
        "confidence_value": 0.65,
        "citation_count": 1,
        "human_validated": False,
    },
)
verdict = response.json()
print(verdict["compliant"], verdict["blocking_reasons"])
```
