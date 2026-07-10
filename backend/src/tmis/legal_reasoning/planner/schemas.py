from dataclasses import dataclass
from enum import Enum


class PlanStepKind(str, Enum):
    """The fixed stages of one reasoning run (see
    docs/25-legal-reasoning.md — Reasoning Orchestrator)."""

    ANALYZE_CASE = "analyze_case"
    SEARCH_RESEARCH = "search_research"
    EXTRACT_FACTS = "extract_facts"
    BUILD_HYPOTHESES = "build_hypotheses"
    GATHER_ARGUMENTS = "gather_arguments"
    GATHER_COUNTER_ARGUMENTS = "gather_counter_arguments"
    EVALUATE_CONFIDENCE = "evaluate_confidence"
    DETECT_CONFLICTS = "detect_conflicts"
    SYNTHESIZE = "synthesize"


@dataclass(frozen=True, slots=True)
class PlanStep:
    kind: PlanStepKind
    description: str


@dataclass(frozen=True, slots=True)
class ReasoningPlan:
    """The ordered plan a `ReasoningOrchestrator` run follows. Fixed for
    Sprint 6 (see the prompt's minimal workflow); kept as an explicit
    object rather than inlined so a future planner can reorder or skip
    steps for a given question without the orchestrator itself changing.
    """

    question: str
    case_id: str | None
    steps: tuple[PlanStep, ...]
