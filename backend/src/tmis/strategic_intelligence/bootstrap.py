from functools import lru_cache

from tmis.ai_governance.bootstrap import get_human_validation_engine
from tmis.ai_governance.human_validation.engine import HumanValidationEngine
from tmis.cabinet_knowledge.bootstrap import get_playbook_engine, get_recommendation_engine
from tmis.cabinet_knowledge.playbooks.engine import PlaybookEngine
from tmis.cabinet_knowledge.recommendations.engine import RecommendationEngine
from tmis.strategic_intelligence.action_planner.engine import ActionPlannerEngine
from tmis.strategic_intelligence.action_planner.store import InMemoryActionPlanStore
from tmis.strategic_intelligence.decision_support.engine import DecisionSupportEngine
from tmis.strategic_intelligence.evaluation.engine import StrategicIntelligenceEvaluator
from tmis.strategic_intelligence.evaluation.sinks import InMemoryStrategicMetricsSink
from tmis.strategic_intelligence.evidence_gap.engine import EvidenceGapEngine
from tmis.strategic_intelligence.hypothesis_lab.engine import HypothesisLabEngine
from tmis.strategic_intelligence.hypothesis_lab.store import InMemoryHypothesisLabStore
from tmis.strategic_intelligence.learning.engine import LearningEngine
from tmis.strategic_intelligence.learning.store import InMemoryLearningStore
from tmis.strategic_intelligence.opportunity_engine.engine import OpportunityEngine
from tmis.strategic_intelligence.overview import StrategicIntelligencePlatform
from tmis.strategic_intelligence.playbooks.adapter import PlaybookAdapter
from tmis.strategic_intelligence.probability.engine import ProbabilityEngine
from tmis.strategic_intelligence.recommendations.engine import StrategicRecommendationEngine
from tmis.strategic_intelligence.review.adapter import StrategyReviewAdapter
from tmis.strategic_intelligence.risk_matrix.engine import RiskMatrixEngine
from tmis.strategic_intelligence.scenario_builder.engine import ScenarioBuilderEngine
from tmis.strategic_intelligence.simulation.engine import SimulationEngine
from tmis.strategic_intelligence.strategy_engine.engine import StrategyEngine
from tmis.strategic_intelligence.timeline.engine import TimelineEngine
from tmis.strategic_intelligence.tradeoffs.engine import TradeoffEngine


@lru_cache
def get_strategy_engine() -> StrategyEngine:
    """Process-wide composition root for `tmis.strategic_intelligence`
    (see docs/86-architecture-strategic-intelligence.md)."""
    return StrategyEngine()


@lru_cache
def get_hypothesis_lab_engine() -> HypothesisLabEngine:
    return HypothesisLabEngine(InMemoryHypothesisLabStore())


@lru_cache
def get_scenario_builder_engine() -> ScenarioBuilderEngine:
    return ScenarioBuilderEngine()


@lru_cache
def get_risk_matrix_engine() -> RiskMatrixEngine:
    return RiskMatrixEngine()


@lru_cache
def get_opportunity_engine() -> OpportunityEngine:
    return OpportunityEngine()


@lru_cache
def get_evidence_gap_engine() -> EvidenceGapEngine:
    return EvidenceGapEngine()


@lru_cache
def get_action_planner_engine() -> ActionPlannerEngine:
    return ActionPlannerEngine(InMemoryActionPlanStore())


@lru_cache
def get_decision_support_engine() -> DecisionSupportEngine:
    return DecisionSupportEngine()


@lru_cache
def get_timeline_engine() -> TimelineEngine:
    return TimelineEngine()


@lru_cache
def get_probability_engine() -> ProbabilityEngine:
    return ProbabilityEngine()


@lru_cache
def get_simulation_engine() -> SimulationEngine:
    return SimulationEngine()


@lru_cache
def get_tradeoff_engine() -> TradeoffEngine:
    return TradeoffEngine()


@lru_cache
def get_playbook_adapter() -> PlaybookAdapter:
    playbook_engine: PlaybookEngine = get_playbook_engine()
    return PlaybookAdapter(playbook_engine)


@lru_cache
def get_strategic_recommendation_engine() -> StrategicRecommendationEngine:
    recommendation_engine: RecommendationEngine = get_recommendation_engine()
    return StrategicRecommendationEngine(recommendation_engine)


@lru_cache
def get_strategy_review_adapter() -> StrategyReviewAdapter:
    human_validation_engine: HumanValidationEngine = get_human_validation_engine()
    return StrategyReviewAdapter(human_validation_engine)


@lru_cache
def get_learning_engine() -> LearningEngine:
    return LearningEngine(InMemoryLearningStore())


@lru_cache
def get_strategic_metrics_sink() -> InMemoryStrategicMetricsSink:
    return InMemoryStrategicMetricsSink()


@lru_cache
def get_strategic_intelligence_evaluator() -> StrategicIntelligenceEvaluator:
    return StrategicIntelligenceEvaluator([get_strategic_metrics_sink()])


@lru_cache
def get_strategic_intelligence_platform() -> StrategicIntelligencePlatform:
    return StrategicIntelligencePlatform(
        get_hypothesis_lab_engine(),
        get_action_planner_engine(),
        get_strategy_review_adapter(),
        get_learning_engine(),
    )
