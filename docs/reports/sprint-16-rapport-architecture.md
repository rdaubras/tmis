# Rapport d'architecture — Sprint 16 (Strategic Litigation & Advisory Intelligence)

## Résumé

Le Sprint 16 ajoute `backend/src/tmis/strategic_intelligence/` (17
sous-modules + une façade + une couche API) au-dessus du socle
existant. Aucun module métier des Sprints 2-15 n'a été modifié ; seul
`tmis/api/v1/router.py` a été touché hors `strategic_intelligence/`,
pour brancher le nouveau routeur REST.

## Conformité aux principes architecturaux

- **Clean Architecture / DDD / SOLID** : chaque sous-module suit le
  patron `schemas.py` → `ports.py` (si persistance dédiée) →
  implémentation(s) → composition dans
  `strategic_intelligence/bootstrap.py`, identique aux sprints
  précédents.
- **Le SLAI ne rend jamais de décision juridique définitive** :
  vérifié structurellement — `Strategy`, `Scenario` et
  `StrategyComparison` ne portent aucun champ `decision`, `winner` ou
  `recommended` ; chaque `Strategy` porte toujours au moins une
  `limitation` rappelant qu'elle reste une proposition.
- **Aucune prédiction de résultat de procès présentée comme
  certaine** : `probability.ProbabilityAssessment` n'exprime qu'une
  vraisemblance qualitative sur un sous-élément, jamais sur l'issue
  globale du dossier ; `simulation.SimulationResult` est purement
  structurel (correspondance de mots-clés) sans aucun champ prédictif.
- **Toutes les interactions IA passent par l'AI Intelligence Fabric** :
  satisfait vacuité — aucun moteur de ce sprint n'appelle un modèle
  brut ; tous sont heuristiques et déterministes, dans la continuité
  de `legal_reasoning.strategy.HeuristicStrategyEngine` et
  `legal_reasoning.hypotheses.HeuristicHypothesisEngine`.
- **Recommandations traçables, explicables, soumises à validation
  humaine** : `review/` réutilise directement
  `ai_governance.human_validation.HumanValidationEngine`, donc chaque
  revue de stratégie apparaît dans les journaux d'audit de l'AI
  Governance Platform (Sprint 15) sans code supplémentaire.

## Décision structurante : `strategy_engine` vs. `legal_reasoning.strategy`

`legal_reasoning.strategy.HeuristicStrategyEngine` (Sprint 6) produit
une `StrategyOption` par hypothèse — une portée locale.
`strategic_intelligence.strategy_engine.StrategyEngine` produit une
`Strategy` par approche globale (négociation, prud'homale,
transactionnelle, procédurale), pouvant mobiliser plusieurs hypothèses
à la fois. Construction neuve plutôt que réutilisation, mais reprise
de la convention de forme (`tuple[str, ...]` en texte libre, jamais de
champ "gagnant").

## Décision structurante : aucune prédiction judiciaire

`probability/` et `simulation/` sont conçus, dès leur schéma, pour
qu'aucun champ prédictif ne puisse exister — vérifié par
`test_probability_assessment_never_scopes_to_case_outcome` et
`test_simulation_engine_never_predicts_an_outcome`. La contrainte est
donc appliquée au niveau du type, pas seulement de la documentation.

## Décision structurante : réutilisation plutôt que réimplémentation

- `playbooks/` enveloppe directement
  `cabinet_knowledge.playbooks.PlaybookEngine` (aucun nouveau
  stockage).
- `recommendations/` compose directement
  `cabinet_knowledge.recommendations.RecommendationEngine.recommend()`.
- `review/` enveloppe directement
  `ai_governance.human_validation.HumanValidationEngine` — pas de
  quatrième réimplémentation du patron d'approbation (après
  `cabinet_knowledge.validation`, `collaboration.approvals` et
  `ai_governance.human_validation`).

## Décision structurante : "jamais de vainqueur désigné"

`decision_support.StrategyComparison` et `tradeoffs.TradeoffAnalysis`
n'ont aucun champ `recommended`/`winner`/`best_strategy_id` —
seulement des métriques côte à côte et un disclaimer. Vérifié par
`test_decision_support_never_ranks_or_recommends` et
`test_tradeoff_engine_never_declares_a_winner`.

## Réutilisation explicite des sprints précédents

- `tmis.cabinet_knowledge.governance` (Sprint 12) — patron
  `ALLOWED_TRANSITIONS`/`InvalidTransitionError`/journal append-only,
  repris pour `hypothesis_lab`.
- `tmis.ai_governance.confidence.GovernanceConfidenceEngine` (Sprint
  15) — patron de facteurs pondérés découplés, réimplémenté localement
  (bounded context distinct) pour `risk_matrix`.
- `tmis.ai_governance.bias_detection.BiasDetectorPort` (Sprint 15) —
  patron de registre extensible, repris pour
  `scenario_builder.ScenarioVariantBuilderPort`.
- `tmis.ai_governance.evaluation.GovernanceEvaluator` (Sprint 15) —
  patron sink-fanout, repris pour
  `evaluation.StrategicIntelligenceEvaluator`.
- `tmis.cabinet_knowledge.feedback.FeedbackEngine` (Sprint 12) —
  patron de taux d'acceptation, repris pour
  `learning.LearningEngine.acceptance_rate_by_type`.
- `tmis.cabinet_knowledge.playbooks.PlaybookEngine`,
  `tmis.cabinet_knowledge.recommendations.RecommendationEngine`,
  `tmis.ai_governance.human_validation.HumanValidationEngine` —
  enveloppés directement, sans nouvelle logique métier.

## Vérification de non-régression

`ruff check src tests` et `mypy src` : aucune erreur sur 1170 fichiers
source (contre 1105 avant ce sprint). `pytest` : **1418 tests passés,
4 ignorés** (contre 1362 avant ce sprint) — 56 tests dédiés à
`strategic_intelligence` (46 unitaires + 10 d'intégration), couverture
globale du dépôt 95,95 %, sans qu'aucun des 1362 tests précédents
n'ait été modifié.

## Voir aussi

- docs/86-architecture-strategic-intelligence.md pour les diagrammes
  Mermaid détaillés.
- docs/reports/sprint-16-demo-strategies.md pour la démonstration
  complète sur trois dossiers fictifs.
