from tmis.ai_governance.human_validation.engine import HumanValidationEngine
from tmis.ai_governance.human_validation.store import InMemoryValidationStore
from tmis.strategic_intelligence.action_planner.engine import ActionPlannerEngine
from tmis.strategic_intelligence.action_planner.store import InMemoryActionPlanStore
from tmis.strategic_intelligence.hypothesis_lab.engine import HypothesisLabEngine
from tmis.strategic_intelligence.hypothesis_lab.store import InMemoryHypothesisLabStore
from tmis.strategic_intelligence.learning.engine import LearningEngine
from tmis.strategic_intelligence.learning.schemas import StrategyOutcome
from tmis.strategic_intelligence.learning.store import InMemoryLearningStore
from tmis.strategic_intelligence.overview import StrategicIntelligencePlatform
from tmis.strategic_intelligence.review.adapter import StrategyReviewAdapter


def _build_platform() -> StrategicIntelligencePlatform:
    return StrategicIntelligencePlatform(
        HypothesisLabEngine(InMemoryHypothesisLabStore()),
        ActionPlannerEngine(InMemoryActionPlanStore()),
        StrategyReviewAdapter(HumanValidationEngine(InMemoryValidationStore())),
        LearningEngine(InMemoryLearningStore()),
    )


def test_case_overview_composes_hypotheses_and_learning_history() -> None:
    platform = _build_platform()
    platform.hypothesis_lab.create("firm-1", "case-1", "Hypothèse A")
    platform.learning.record_outcome(
        "firm-1", "case-1", "strategy-1", "Négociation amiable", StrategyOutcome.CHOSEN, "avocat-1"
    )

    overview = platform.case_overview("firm-1", "case-1")

    assert len(overview.hypotheses) == 1
    assert len(overview.learning_history) == 1


def test_strategy_overview_composes_action_plan_and_review_status() -> None:
    platform = _build_platform()
    platform.action_planner.add_step("firm-1", "strategy-1", "Étape 1", "procédure")

    overview = platform.strategy_overview("firm-1", "strategy-1")

    assert len(overview.action_steps) == 1
    assert overview.is_validated is False
    assert overview.review_history == ()
