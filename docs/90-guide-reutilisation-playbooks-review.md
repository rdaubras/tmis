# Guide — Réutilisation : Playbooks, Recommendations, Review & Learning

Quatre sous-modules du SLAI sont des adaptateurs délibérément fins
autour de moteurs déjà construits dans des sprints précédents, plutôt
que de nouvelles implémentations — conformément à l'instruction du
sprint "réutiliser les playbooks du Cabinet Knowledge Engine" et à la
convention TMIS d'éviter une troisième ou quatrième réimplémentation
du même patron.

## `playbooks/` — enveloppe `cabinet_knowledge.playbooks`

```python
from tmis.strategic_intelligence.bootstrap import get_playbook_adapter

adapter = get_playbook_adapter()
playbooks = adapter.find_playbooks_for_case_type("firm-123", "licenciement")
for playbook in playbooks:
    steps = adapter.steps_as_recommended_actions(playbook)
```

Aucun nouveau stockage : `find_playbooks_for_case_type` délègue
directement à `PlaybookEngine.list_playbooks()`, qui ne retourne que
des playbooks déjà validés.

## `recommendations/` — compose `cabinet_knowledge.recommendations` + `learning`

```python
from tmis.strategic_intelligence.bootstrap import get_strategic_recommendation_engine
from tmis.cabinet_knowledge.recommendations.schemas import RecommendationContext
from tmis.strategic_intelligence.recommendations.schemas import SimilarStrategyRecommendation

engine = get_strategic_recommendation_engine()
recommendations = engine.recommend(
    "firm-123",
    RecommendationContext(domain_tag="licenciement", keywords=("faute grave",)),
    similar_strategies=(
        SimilarStrategyRecommendation("strategy-old-1", "Négociation amiable", "issue favorable"),
    ),
)
```

`knowledge_recommendation_ids` provient directement de
`RecommendationEngine.recommend()` (connaissances validées, toujours
expliquées). `similar_strategies` est fourni par l'appelant plutôt que
recalculé en interne — décision de conception qui garde
`StrategicRecommendationEngine` testable sans fixture d'historique
d'apprentissage.

## `review/` — enveloppe `ai_governance.human_validation`

```python
from tmis.strategic_intelligence.bootstrap import get_strategy_review_adapter
from tmis.ai_governance.human_validation.schemas import ValidationDecisionType

review = get_strategy_review_adapter()
request = review.request_review("firm-123", "strategy-1", "avocat-1", ("associe-1",))
review.decide("firm-123", request.id, "associe-1", ValidationDecisionType.APPROVE)
print(review.is_validated("firm-123", "strategy-1"))  # True
```

L'`id` de la stratégie sert de `production_id` côté
`HumanValidationEngine` : chaque revue de stratégie apparaît donc
automatiquement dans les journaux d'audit de l'AI Governance Platform.

## `learning/` — boucle de rétroaction

`learning.LearningEngine` enregistre ce qui est réellement arrivé à
une stratégie proposée — choisie, validée, rejetée, modifiée — pour
alimenter `recommendations/` avec des "stratégies passées similaires".

```python
from tmis.strategic_intelligence.bootstrap import get_learning_engine
from tmis.strategic_intelligence.learning.schemas import StrategyOutcome

learning = get_learning_engine()
learning.record_outcome(
    "firm-123", "dossier-1", "strategy-1", "Négociation amiable",
    StrategyOutcome.CHOSEN, actor="avocat-1",
)
print(learning.acceptance_rate_by_type("firm-123"))
```
