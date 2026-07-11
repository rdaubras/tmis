# Guide — Router

`tmis.ai_fabric.router.RouterEngine` est le seul endroit où TMIS
choisit un modèle pour une tâche donnée.

## Construire une requête de routage

```python
from tmis.ai_fabric.model_profiles.schemas import ModelProfile
from tmis.ai_fabric.router.schemas import RoutingRequest

request = RoutingRequest(
    firm_id="firm-123",
    task_type="Rédaction",
    prompt="Rédige un avis sur ce bail commercial.",
    profile=ModelProfile.DRAFTING,   # None = tous les profils
    target_cost_usd=0.03,            # None = pas de contrainte de coût
    max_latency_ms=1500,             # None = pas de contrainte de latence
    min_quality_score=0.7,           # 0.0 = pas de contrainte de qualité
    country="FR",                    # pour les politiques COUNTRY_RESTRICTED
    data_type="contract",            # pour les politiques DATA_TYPE_RESTRICTED
)
```

## Router

```python
from tmis.ai_fabric.bootstrap import get_router_engine

decision = get_router_engine().route(request)
print(decision.model.name)
print(decision.reasons)   # explicabilité : une phrase par étape de filtrage
```

## Ordre des filtres

1. Profil (`list_by_profile` ou tous les modèles)
2. Disponibilité (`ModelDescriptor.availability`)
3. Niveau de qualité minimal
4. Coût cible
5. Latence maximale
6. Gouvernance (`tmis.ai_fabric.governance`, par modèle)
7. Quota du cabinet (`tmis.ai_fabric.quotas`)

Le modèle retenu parmi les candidats restants est celui qui maximise
`(quality_score, -cost_per_1k_tokens_usd, -avg_latency_ms)` — à
qualité égale, le moins cher gagne ; à qualité et coût égaux, le plus
rapide gagne.

## Erreurs

- `NoEligibleModelError` — aucun modèle ne satisfait tous les filtres ;
  `.reasons` explique chaque exclusion.
- `QuotaExceededError` — le cabinet a atteint son quota d'appels.

## Étendre le routeur

N'ajoutez jamais de connaissance d'un fournisseur spécifique dans
`RouterEngine` — toute nouvelle contrainte doit s'exprimer en termes
de `ModelDescriptor` (un champ déjà présent, ou une nouvelle méthode
`_filter_*` suivant le même patron que les méthodes existantes).
