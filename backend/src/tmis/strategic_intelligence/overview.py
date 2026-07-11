from dataclasses import dataclass, field

from tmis.ai_governance.human_validation.schemas import ValidationRequest
from tmis.strategic_intelligence.action_planner.engine import ActionPlannerEngine
from tmis.strategic_intelligence.action_planner.schemas import ActionStep
from tmis.strategic_intelligence.hypothesis_lab.engine import HypothesisLabEngine
from tmis.strategic_intelligence.hypothesis_lab.schemas import StrategicHypothesis
from tmis.strategic_intelligence.learning.engine import LearningEngine
from tmis.strategic_intelligence.learning.schemas import LearningRecord
from tmis.strategic_intelligence.review.adapter import StrategyReviewAdapter


@dataclass(frozen=True, slots=True)
class CaseStrategicOverview:
    """Every hypothesis and past strategic outcome recorded for a case
    — the entry point for "où en est ce dossier sur le plan
    stratégique ?"."""

    case_id: str
    hypotheses: tuple[StrategicHypothesis, ...] = field(default_factory=tuple)
    learning_history: tuple[LearningRecord, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class StrategyOverview:
    """Every actionable and governance fact attached to one strategy —
    its action plan and its human-review status. Never includes a
    "recommended" or "chosen" field: consulting this overview does not
    constitute a decision."""

    strategy_id: str
    action_steps: tuple[ActionStep, ...] = field(default_factory=tuple)
    review_history: tuple[ValidationRequest, ...] = field(default_factory=tuple)
    is_validated: bool = False


class StrategicIntelligencePlatform:
    """The single entry point composing the sprint's *persisted*
    engines (`hypothesis_lab`, `action_planner`, `review`, `learning`)
    into one read — mirrors `ai_governance.overview.AIGovernancePlatform`'s
    role. The stateless engines (`strategy_engine`, `risk_matrix`,
    `scenario_builder`, `opportunity_engine`, `evidence_gap`,
    `timeline`, `probability`, `simulation`, `tradeoffs`,
    `decision_support`, `playbooks`, `recommendations`) are not
    composed here — they take pre-computed inputs and return fresh
    results per call, so there is nothing to look up by id."""

    def __init__(
        self,
        hypothesis_lab: HypothesisLabEngine,
        action_planner: ActionPlannerEngine,
        review: StrategyReviewAdapter,
        learning: LearningEngine,
    ) -> None:
        self.hypothesis_lab = hypothesis_lab
        self.action_planner = action_planner
        self.review = review
        self.learning = learning

    def case_overview(self, firm_id: str, case_id: str) -> CaseStrategicOverview:
        return CaseStrategicOverview(
            case_id=case_id,
            hypotheses=tuple(self.hypothesis_lab.list_for_case(firm_id, case_id)),
            learning_history=tuple(self.learning.history_for_case(firm_id, case_id)),
        )

    def strategy_overview(self, firm_id: str, strategy_id: str) -> StrategyOverview:
        return StrategyOverview(
            strategy_id=strategy_id,
            action_steps=tuple(self.action_planner.list_for_strategy(firm_id, strategy_id)),
            review_history=tuple(self.review.history(firm_id, strategy_id)),
            is_validated=self.review.is_validated(firm_id, strategy_id),
        )
