from tmis.legal_reasoning.planner.planner import HeuristicReasoningPlanner
from tmis.legal_reasoning.planner.schemas import PlanStepKind


def test_build_plan_carries_question_and_case_id() -> None:
    plan = HeuristicReasoningPlanner().build_plan("Le licenciement est-il fondé ?", "case-1")
    assert plan.question == "Le licenciement est-il fondé ?"
    assert plan.case_id == "case-1"


def test_build_plan_follows_the_fixed_workflow_order() -> None:
    plan = HeuristicReasoningPlanner().build_plan("question", None)
    assert [step.kind for step in plan.steps] == [
        PlanStepKind.ANALYZE_CASE,
        PlanStepKind.SEARCH_RESEARCH,
        PlanStepKind.EXTRACT_FACTS,
        PlanStepKind.BUILD_HYPOTHESES,
        PlanStepKind.GATHER_ARGUMENTS,
        PlanStepKind.GATHER_COUNTER_ARGUMENTS,
        PlanStepKind.EVALUATE_CONFIDENCE,
        PlanStepKind.DETECT_CONFLICTS,
        PlanStepKind.SYNTHESIZE,
    ]


def test_build_plan_accepts_no_case_id() -> None:
    plan = HeuristicReasoningPlanner().build_plan("question", None)
    assert plan.case_id is None
