# Guide — Ajouter un modèle

## 1. Décrire le modèle

```python
from tmis.ai_fabric.capabilities.schemas import Capability
from tmis.ai_fabric.model_profiles.schemas import ModelProfile
from tmis.ai_fabric.model_registry.schemas import ModelDescriptor

descriptor = ModelDescriptor(
    name="mon-modele-v2",
    version="2024-11",
    provider="my-provider",           # doit exister dans provider_registry
    cost_per_1k_tokens_usd=0.015,
    avg_latency_ms=650,
    max_context_tokens=64_000,
    capabilities=frozenset({Capability.TEXT_COMPLETION, Capability.LONG_CONTEXT}),
    profiles=frozenset({ModelProfile.REASONING, ModelProfile.DRAFTING}),
    quality_score=0.80,     # [0, 1] — affiné automatiquement par le Benchmark Engine ensuite
    legal_score=0.75,
    drafting_score=0.82,
    research_score=0.70,
    reasoning_score=0.78,
)
```

## 2. L'enregistrer

```python
from tmis.ai_fabric.bootstrap import get_model_registry

get_model_registry().register(descriptor)
```

En production, ajoutez le descripteur à
`tmis.ai_fabric.model_registry.seed._DEFAULT_MODELS` pour qu'il soit
seedé au démarrage du processus, ou enregistrez-le via un script
d'administration séparé.

## 3. Vérifier son admissibilité au routage

Le routeur ne considère un modèle que s'il est **disponible**
(`availability=True`, valeur par défaut), **non exclu par une
politique de gouvernance** (voir docs/62-guide-gouvernance.md pour le
motif équivalent côté Cabinet Knowledge, et
`tmis.ai_fabric.governance` pour ce sprint), et compatible avec les
contraintes de la requête (coût cible, latence maximale, niveau de
qualité minimal).

## 4. Laisser le Benchmark Engine affiner le score de qualité

`quality_score` n'est pas figé : chaque appel à
`BenchmarkEngine.run(model_name, texte, cost_usd=..., latency_ms=...)`
fait évoluer `ModelDescriptor.quality_score` par moyenne mobile — voir
docs/77-guide-benchmark.md.
