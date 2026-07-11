# Tableau comparatif des modèles configurés (Sprint 14)

Généré depuis le catalogue seedé par
`tmis.ai_fabric.model_registry.seed.seed_default_models` — les valeurs
`quality_score` évoluent ensuite automatiquement à chaque appel de
`BenchmarkEngine.run()` (voir docs/77-guide-benchmark.md), le tableau
ci-dessous reflète l'état initial du catalogue.

| Modèle | Version | Fournisseur | Coût / 1k tokens | Latence moy. | Contexte max | Capacités | Profils | Qualité | Juridique | Rédaction | Recherche | Raisonnement |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| claude-legal | 4.5 | anthropic | $0.024 | 1000 ms | 200 000 | long_context, streaming, text_completion | drafting, reasoning, synthesis | 0.91 | 0.88 | 0.90 | 0.82 | 0.90 |
| gpt-4-legal | 2024-08 | openai | $0.03 | 1200 ms | 128 000 | function_calling, long_context, text_completion | drafting, reasoning, synthesis | 0.90 | 0.85 | 0.88 | 0.80 | 0.87 |
| embed-small | 3-small | openai | $0.0001 | 200 ms | 8 000 | embeddings | embeddings | 0.75 | 0.50 | 0.20 | 0.60 | 0.20 |
| local-ocr | 1.0 | local | $0.0 | 2000 ms | 4 000 | ocr | ocr | 0.70 | 0.50 | 0.30 | 0.40 | 0.30 |
| local-vision | 1.0 | local | $0.0 | 2500 ms | 4 000 | vision | vision | 0.68 | 0.45 | 0.30 | 0.40 | 0.30 |
| mistral-fast | large-2 | mistral | $0.002 | 400 ms | 32 000 | text_completion | classification, translation | 0.65 | 0.55 | 0.55 | 0.55 | 0.55 |

## Couverture par profil (pipeline par défaut du Planner)

| Profil requis par le pipeline | Modèle(s) éligible(s) |
|---|---|
| VISION (Analyse documentaire) | local-vision |
| OCR (Extraction) | local-ocr |
| SYNTHESIS (Recherche) | claude-legal, gpt-4-legal |
| REASONING (Raisonnement) | claude-legal, gpt-4-legal |
| DRAFTING (Rédaction) | claude-legal, gpt-4-legal |
| — (Contrôle) | aucun — exécuté par `CriticModel`, qui n'appelle aucun modèle |

Chaque profil du pipeline par défaut dispose d'au moins un modèle
éligible — `TaskPlanner.plan()` produit donc une décision de routage
complète pour les cinq premières étapes, vérifié par
`test_bootstrap_seeds_a_model_for_every_default_pipeline_profile`
(tests/integration/ai_fabric/).

## Lecture

- **claude-legal** est le meilleur choix par défaut pour
  raisonnement/rédaction/synthèse (score qualité et scores
  spécialisés les plus élevés), mais aussi le plus coûteux hors
  gpt-4-legal.
- **mistral-fast** est réservé à la classification/traduction — pas
  éligible aux profils de rédaction ou raisonnement, son score qualité
  global (0.65) resterait de toute façon en dessous d'un seuil
  `min_quality_score` raisonnable pour ces usages.
- **local-ocr**/**local-vision** ont un coût nul (modèles locaux) mais
  une latence nettement supérieure — cohérent avec des modèles
  d'inférence locale plutôt qu'API distante.
- **embed-small** n'est éligible à aucune étape du pipeline par défaut
  (aucune étape ne demande le profil `EMBEDDINGS`) — disponible pour
  les futurs cas d'usage de recherche sémantique
  (`tmis.legal_research`, `tmis.cabinet_knowledge.search`).
