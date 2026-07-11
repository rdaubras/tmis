# Rapport d'architecture — Sprint 15 (AI Governance & Explainability Platform)

## Résumé

Le Sprint 15 ajoute `backend/src/tmis/ai_governance/` (18 sous-modules
+ une façade + un bus d'événements dédié + une couche API) au-dessus
du socle existant. Aucun module métier des Sprints 2-14 n'a été
modifié ; seul `tmis/api/v1/router.py` a été touché hors
`ai_governance/`, pour brancher le nouveau routeur REST.

## Conformité aux principes architecturaux

- **Clean Architecture / DDD / SOLID** : chaque sous-module suit le
  patron `schemas.py` → `ports.py` (si persistance dédiée) →
  implémentation(s) → composition dans `ai_governance/bootstrap.py`,
  identique aux sprints précédents.
- **Event Driven Architecture** : `ai_governance/events.py` définit
  `GovernanceEvent`/`GovernanceEventBus`, sa propre hiérarchie
  d'événements — mirroir de
  `tmis.collaboration.event_bus.CollaborationEvent`, délibérément
  indépendante de `tmis.ai.events` pour ne créer aucune dépendance
  imposée dans un sens ou dans l'autre.
- **Toutes les productions IA restent explicables, traçables,
  gouvernées et auditables** : vérifié par la façade
  `AIGovernancePlatform.overview()`, qui répond en une lecture aux
  neuf questions de la Vision du sprint (voir
  docs/reports/sprint-15-demo-explicabilite.md pour une démonstration
  complète).
- **Aucune réponse IA définitive sans respecter les politiques du
  cabinet** : `ComplianceEngine.check()` combine
  `policy_engine.evaluate()` et `risk_engine.assess()` en un verdict
  unique ; la démonstration du sprint montre concrètement un export
  bloqué avant validation humaine puis autorisé après.

## Décision structurante : gouvernance de sortie vs. gouvernance de modèle

`tmis.ai_fabric.governance` (Sprint 14) décide quel **modèle** peut
être appelé ; `tmis.ai_governance.policy_engine` gouverne la
**production déjà générée**. Les deux portent le même rôle
architectural (`GovernanceEngine`/`PolicyEngine` historisant des
décisions avec `reasons` toujours non vides) dans deux bounded
contexts distincts — un troisième `GovernanceEngine`-shaped existe
déjà dans `tmis.cabinet_knowledge.governance` (Sprint 12). Ce n'est
pas une collision accidentelle mais une convention assumée du
projet : des noms de rôle identiques, des portées différentes,
documentées explicitement dans chaque docstring.

## Décision structurante : entrées découplées

`confidence`, `quality` et `explainability` ne font aucun import
croisé vers `provenance`/`risk_engine`/`human_validation` — ils
reçoivent des facteurs déjà calculés en paramètres. C'est la façade
`AIGovernancePlatform` (ou l'appelant métier) qui assemble ces
facteurs avant de les transmettre. Ce choix, déjà présent dans
`tmis.legal_reasoning.confidence`, garde chaque moteur testable
isolément sans mock d'autres bounded contexts.

## Décision structurante : validation hiérarchique

`tmis.collaboration.approvals` (Sprint 8) ne connaît que `SINGLE` et
`MULTIPLE`. Le sprint demandait explicitement une validation
hiérarchique — introduite ici comme un mode inédit dans TMIS :
`HIERARCHICAL` avance à travers des niveaux ordonnés
(`approver_tiers: tuple[tuple[str, ...], ...]`), chaque niveau
nécessitant au moins une approbation avant de considérer le niveau
suivant. Un rejet à n'importe quel niveau fait basculer l'ensemble à
`REJECTED`, cohérent avec le comportement de
`collaboration.approvals`. Vérifié par
`test_hierarchical_validation_advances_tier_by_tier` et son pendant
d'intégration via l'API.

## Réutilisation explicite des sprints précédents

- `tmis.ai_fabric.evaluation.ResponseEvaluator`/`jaccard_similarity`
  (Sprint 14) — `hallucination_detection` s'appuie directement dessus
  pour le comptage de citations et la détection de contradictions.
- `tmis.cabinet_knowledge.lineage.LineageEngine`/`LineageExplanation`
  (Sprint 12) — modèle direct pour `ai_governance.lineage`.
- `tmis.legal_reasoning.confidence.ConfidenceWeights` — patron de
  facteurs pondérés normalisables, repris pour
  `GovernanceConfidenceWeights`.
- `tmis.legal_reasoning.decision_graph` — inspiration pour la vue
  graphe de `reasoning_chain.to_graph()`.
- `tmis.collaboration.approvals.ApprovalEngine` — patron
  générique `target_type`/`target_id`/historique, base du mode
  `SIMPLE`/`MULTIPLE` de `human_validation` (avant extension
  `HIERARCHICAL`).

## Vérification de non-régression

`ruff check src tests` et `mypy src` : aucune erreur sur 1105 fichiers
source (contre 1021 avant ce sprint). `pytest` : **1362 tests passés,
4 ignorés** (contre 1272 avant ce sprint) — 90 tests dédiés à
`ai_governance` (78 unitaires + 12 d'intégration), couverture globale
du dépôt 96,13 %, sans qu'aucun des 1272 tests précédents n'ait été
modifié.

## Voir aussi

- docs/80-architecture-ai-governance.md pour les diagrammes Mermaid
  détaillés (pipeline de la chaîne de raisonnement, séquence du
  verdict de conformité).
- docs/reports/sprint-15-demo-explicabilite.md pour la démonstration
  complète de la chaîne d'explicabilité sur un dossier fictif.
