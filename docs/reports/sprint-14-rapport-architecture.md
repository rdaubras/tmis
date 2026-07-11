# Rapport d'architecture — Sprint 14 (AI Intelligence Fabric)

## Résumé

Le Sprint 14 ajoute `backend/src/tmis/ai_fabric/` (26 sous-modules +
une couche API) au-dessus du socle existant. Aucun module métier des
Sprints 2-13 n'a été modifié ; seul `tmis/api/v1/router.py` a été
touché hors `ai_fabric/`, pour brancher le nouveau routeur REST.

## Conformité aux principes architecturaux

- **Clean Architecture / DDD / SOLID** : chaque sous-module suit le
  patron `schemas.py` → `ports.py` (si persistance dédiée) →
  implémentation(s) → composition dans `ai_fabric/bootstrap.py`,
  identique aux sprints précédents.
- **Toutes les interactions IA passent par la Fabric** : `fabric.py`
  expose une façade unique (`AIIntelligenceFabric`) composant router,
  planner, critic, comparison, consensus et fusion — un module métier
  n'a besoin d'importer que cette façade.
- **Aucun module métier ne connaît un fournisseur** : vérifié
  architecturalement — `provider_registry` est le seul point de
  contact avec `tmis.ai.providers`, et rien dans `router`, `planner`,
  `critic`, `comparison`, `consensus` ou `fusion` n'importe
  `tmis.ai.providers` directement.
- **Décisions de routage explicables** : `RoutingDecision.reasons`
  accumule une phrase par étape de filtrage (profil, disponibilité,
  qualité, coût, latence, gouvernance, sélection finale) — vérifié
  par `test_router_decision_is_explainable`.
- **Fonctionnement même si un fournisseur est indisponible** :
  `fallback.FallbackEngine` résout un modèle secondaire quand le
  modèle principal est indisponible ou non enregistré, et le routeur
  lui-même filtre systématiquement sur `availability` avant toute
  autre contrainte.

## Décision structurante : réutilisation du registre de fournisseurs

`ai_fabric.provider_registry` ré-exporte
`tmis.ai.providers.registry.ProviderRegistry` (Sprint 2) au lieu de
créer un second registre. `model_registry` ajoute uniquement les
métadonnées manquantes (coût, latence, scores) — décision documentée
explicitement dans le docstring du module.

## Décision structurante : capacités techniques vs. profils sémantiques

`Capability` (technique) et `ModelProfile` (sémantique) sont deux
vocabulaires indépendants, satisfaisant explicitement l'exigence du
sprint "chaque profil doit pouvoir évoluer indépendamment".

## Décision structurante : le Critic ne génère jamais

`CriticModel` ne fait aucun appel réseau ni ne produit de texte — il
consomme uniquement les métriques déterministes de
`evaluation.ResponseEvaluator` (citations par expression régulière,
contradictions par similarité de Jaccard entre phrases de polarité
opposée). La dernière étape du pipeline par défaut du Planner
("Contrôle") route donc vers `CriticModel`, jamais vers un modèle —
vérifié par `test_planner_follows_the_sprint_default_pipeline`.

## Décision structurante : quotas comme garde-fou dur

Contrairement à `CostTrackerEngine.check_thresholds` (Sprint 10, qui
alerte seulement), `QuotaEngine.check()` bloque effectivement le
routage via `QuotaExceededError` avant que le routeur n'accepte de
considérer un modèle — les deux mécanismes coexistent avec des
responsabilités distinctes et documentées.

## Bug trouvé et corrigé pendant le développement

Le premier jet de `governance.engine.GovernanceEngine` construisait
correctement une `PolicyDecision` dans `evaluate()`, mais appelait
ensuite une méthode `evaluate_and_record()` distincte référençant un
`_policy_store_append()` inexistant — confusion entre le magasin de
politiques (`PolicyStorePort`) et le magasin d'audit
(`GovernanceStorePort`, jamais injecté dans le constructeur à ce
stade). **Corrigé** avant toute exécution de `ruff`/`mypy` : ajout du
troisième paramètre `governance_store` au constructeur, fusion de la
logique de persistance directement dans `evaluate(..., record=True)`,
suppression des méthodes brisées, ajout de `history()`. Le
comportement final est fixé par
`test_evaluate_records_decision_in_history_by_default` et
`test_evaluate_with_record_false_does_not_persist`
(tests/unit/ai_fabric/).

## Réutilisation explicite des sprints précédents

- `tmis.ai.providers.registry.ProviderRegistry` (Sprint 2) —
  `provider_registry`.
- `tmis.ai.prompts.registry.PromptRegistry` (Sprint 2) —
  `prompt_optimizer`, conformément à l'exigence du sprint que les
  prompts restent versionnés dans le Prompt Registry.
- `tmis.ai.cache.ports.CachePort`/`InMemoryCache` (Sprint 2) —
  backend de `cache.ResponseCache`.
- `tmis.platform.cost_control.CostTrackerEngine` (Sprint 10) —
  enveloppé par `token_manager` plutôt que réimplémenté.
- `tmis.platform.licensing.LicenseEngine.has_feature` (Sprint 10) —
  gate `ENTERPRISE_ONLY` dans `governance`.
- `tmis.platform.performance.concurrency.bounded_gather` (Sprint 10)
  — parallélisme borné dans `latency_optimizer` et `batch`.

## Vérification de non-régression

`ruff check src tests` et `mypy src` : aucune erreur sur 1021 fichiers
source (contre 934 avant ce sprint). `pytest` : **1272 tests passés, 4
ignorés** (contre 1169 avant ce sprint) — 103 tests dédiés à
`ai_fabric` (85 unitaires + 18 d'intégration), couverture du module
98 %, couverture globale du dépôt 96 %, sans qu'aucun des 1169 tests
précédents n'ait été modifié.

## Voir aussi

- docs/73-architecture-ai-fabric.md pour les diagrammes Mermaid
  détaillés (pipeline du Planner, séquence de décision du Router).
- docs/reports/sprint-14-comparatif-modeles.md pour le tableau
  comparatif des modèles configurés.
