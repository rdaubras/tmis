# Guide — Benchmark Engine

`tmis.ai_fabric.benchmark.BenchmarkEngine` mesure une réponse produite
par un modèle et fait automatiquement évoluer le routeur — aucune
étape manuelle n'est nécessaire pour que le routage en tienne compte.

## Lancer une mesure

```python
from tmis.ai_fabric.bootstrap import get_benchmark_engine

run = get_benchmark_engine().run(
    "gpt-4-legal",
    response_text,      # le texte réellement produit par le modèle
    cost_usd=0.021,      # coût réel de l'appel
    latency_ms=1180,     # latence réellement observée
)
print(run.quality_score, run.hallucination_flags, run.token_count)
```

## Ce qui est mesuré

| Métrique | Calcul |
|---|---|
| `quality_score` | cohérence (`ResponseEvaluator`) pénalisée par le nombre de contradictions détectées |
| `hallucination_flags` | nombre de contradictions internes détectées dans la réponse |
| `token_count` | heuristique de comptage de mots (`estimate_tokens`) |
| `cost_usd` / `latency_ms` | fournis par l'appelant (mesurés au moment de l'appel réel) |

## Alimentation automatique du routeur

Chaque `run()` met à jour `ModelDescriptor.quality_score` par moyenne
mobile exponentielle (facteur 0,3) :

```
nouveau_score = 0.7 × ancien_score + 0.3 × score_mesuré
```

Le routeur (`tmis.ai_fabric.router`) lit toujours
`ModelDescriptor.quality_score` au moment de router — il n'y a donc
rien à faire pour que "les résultats alimentent automatiquement le
routeur", comme l'exige l'énoncé du sprint.

## Consulter l'historique

```python
get_benchmark_engine().history("gpt-4-legal")       # tous les runs pour ce modèle
get_benchmark_engine().comparison_table()             # dernier run de chaque modèle, trié par qualité
```

Ces deux méthodes sont exposées respectivement par
`GET /api/v1/ai-fabric/benchmark/{model_name}` et
`GET /api/v1/ai-fabric/benchmark`.
