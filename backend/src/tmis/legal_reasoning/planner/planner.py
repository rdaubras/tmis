from tmis.legal_reasoning.planner.schemas import PlanStep, PlanStepKind, ReasoningPlan

_FIXED_STEPS: tuple[PlanStep, ...] = (
    PlanStep(PlanStepKind.ANALYZE_CASE, "Analyse du dossier"),
    PlanStep(PlanStepKind.SEARCH_RESEARCH, "Recherche documentaire"),
    PlanStep(PlanStepKind.EXTRACT_FACTS, "Extraction des faits"),
    PlanStep(PlanStepKind.BUILD_HYPOTHESES, "Construction des hypothèses"),
    PlanStep(PlanStepKind.GATHER_ARGUMENTS, "Recherche des arguments"),
    PlanStep(PlanStepKind.GATHER_COUNTER_ARGUMENTS, "Recherche des contre-arguments"),
    PlanStep(PlanStepKind.EVALUATE_CONFIDENCE, "Évaluation de la confiance"),
    PlanStep(PlanStepKind.DETECT_CONFLICTS, "Détection des contradictions"),
    PlanStep(PlanStepKind.SYNTHESIZE, "Synthèse"),
)


class HeuristicReasoningPlanner:
    """Implements `ReasoningPlannerPort` with the fixed Sprint 6 workflow
    (see docs/25-legal-reasoning.md). The plan is returned as data (not
    just executed inline) so `ReasoningOrchestrator` can log/expose which
    steps a run went through, and so a future planner can vary the plan
    per question without changing the orchestrator.
    """

    def build_plan(self, question: str, case_id: str | None) -> ReasoningPlan:
        return ReasoningPlan(question=question, case_id=case_id, steps=_FIXED_STEPS)
