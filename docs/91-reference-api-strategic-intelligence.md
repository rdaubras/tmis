# Référence API — Strategic Litigation & Advisory Intelligence (Sprint 16)

Base : `/api/v1/strategic-intelligence`. Documentation interactive
complète sur `/docs` (OpenAPI, généré automatiquement par FastAPI).

## Stratégies

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/strategies/generate` | génère plusieurs stratégies coexistantes pour une question |

## Hypothesis Lab

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/hypotheses` | crée une hypothèse |
| `GET` | `/hypotheses/{case_id}` | `?firm_id=...` — hypothèses du dossier |
| `POST` | `/hypotheses/compare` | similarité + termes partagés + différences |
| `POST` | `/hypotheses/merge` | fusionne deux hypothèses (les originales passent à `MERGED`) |
| `POST` | `/hypotheses/{hypothesis_id}/invalidate` | invalide une hypothèse (avec motif) |
| `POST` | `/hypotheses/{hypothesis_id}/archive` | archive une hypothèse |
| `GET` | `/hypotheses/{hypothesis_id}/history` | `?firm_id=...` — journal historisé des transitions |

## Scénarios & risques

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/scenarios` | construit les scénarios what-if (favorable/défavorable/intermédiaire) |
| `POST` | `/risk-matrix/evaluate` | score de risque pondéré, toujours expliqué |

## Opportunités & preuves manquantes

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/opportunities` | arguments inexploités, documents complémentaires, clauses à vérifier |
| `POST` | `/evidence-gaps` | éléments de preuve manquants, classés par impact estimé |

## Plan d'action

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/action-plan/steps` | ajoute une étape |
| `DELETE` | `/action-plan/steps/{step_id}` | `?firm_id=...` — supprime une étape |
| `POST` | `/action-plan/steps/{step_id}/done` | `?firm_id=&done=` — marque une étape faite/non faite |
| `POST` | `/action-plan/reorder` | réordonne les étapes |
| `GET` | `/action-plan/{strategy_id}` | `?firm_id=...` — plan complet, trié par ordre |

## Comparaison & compromis

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/decision-support/compare` | tableau de métriques côte à côte, jamais de vainqueur |
| `POST` | `/tradeoffs/compare` | comparaison par paire, avantages + risques partagés |

## Chronologie, vraisemblance & simulation

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/timeline/build` | fusionne et trie une chronologie stratégique |
| `POST` | `/probability/assess` | vraisemblance qualitative d'un sous-élément (jamais du procès) |
| `POST` | `/simulation/run` | simulation structurelle par mots-clés, aucune prédiction |

## Playbooks & recommandations

| Méthode | Chemin | Rôle |
|---|---|---|
| `GET` | `/playbooks` | `?firm_id=&case_type=` — playbooks validés du Cabinet Knowledge Engine |

## Revue humaine

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/review/request` | demande de revue (réutilise `ai_governance.human_validation`) |
| `POST` | `/review/{request_id}/decide` | approuver / rejeter / demander une révision |
| `GET` | `/review/{strategy_id}` | `?firm_id=...` — historique des demandes |

## Apprentissage

| Méthode | Chemin | Rôle |
|---|---|---|
| `POST` | `/learning/outcomes` | enregistre l'issue réelle d'une stratégie |
| `GET` | `/learning/{case_id}` | `?firm_id=...` — historique du dossier |
| `GET` | `/learning/acceptance-rate/{firm_id}` | taux d'acceptation par type de stratégie |

## Vue d'ensemble

| Méthode | Chemin | Rôle |
|---|---|---|
| `GET` | `/overview/case/{case_id}` | `?firm_id=...` — hypothèses + historique d'apprentissage |
| `GET` | `/overview/strategy/{strategy_id}` | `?firm_id=...` — plan d'action + statut de revue |

## Codes d'erreur

| Code | Signification |
|---|---|
| `404` | hypothèse, étape ou demande de revue introuvable |
| `400` | transition d'hypothèse invalide |
| `422` | corps de requête invalide (validation Pydantic) |

## Exemple

```python
import httpx

response = httpx.post(
    "https://cabinet.tmis.example.com/api/v1/strategic-intelligence/strategies/generate",
    json={
        "case_id": "dossier-licenciement-2026-03",
        "question": "Comment défendre ce salarié ?",
        "hypotheses": ["Licenciement sans cause réelle et sérieuse"],
        "available_evidence": ["Bulletins de salaire"],
        "missing_evidence": ["Témoignage d'un collègue"],
    },
)
for strategy in response.json():
    print(strategy["strategy_type"], strategy["confidence"], strategy["limitations"])
```
