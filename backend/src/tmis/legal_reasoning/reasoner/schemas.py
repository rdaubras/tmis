from dataclasses import dataclass, field
from datetime import UTC, datetime

from tmis.legal_reasoning.arguments.schemas import Argument
from tmis.legal_reasoning.confidence.schemas import ConfidenceScore
from tmis.legal_reasoning.conflicts.schemas import Conflict
from tmis.legal_reasoning.counter_arguments.schemas import CounterArgument
from tmis.legal_reasoning.decision_graph.schemas import DecisionGraph
from tmis.legal_reasoning.evidence.schemas import ReasoningEvidenceLink
from tmis.legal_reasoning.explanations.schemas import Explanation
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis
from tmis.legal_reasoning.strategy.schemas import StrategyOption


@dataclass
class ReasoningSession:
    """The full, traceable outcome of one reasoning run — the aggregate
    that ties together every LRE² module (see
    docs/25-legal-reasoning.md). Never a final legal document: `synthesis`
    is a transparent summary of the reasoning, not a legal conclusion.
    """

    id: str
    question: str
    case_id: str | None
    hypotheses: list[Hypothesis] = field(default_factory=list)
    arguments: list[Argument] = field(default_factory=list)
    counter_arguments: list[CounterArgument] = field(default_factory=list)
    evidence_links: list[ReasoningEvidenceLink] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    confidence_scores: dict[str, ConfidenceScore] = field(default_factory=dict)
    strategies: list[StrategyOption] = field(default_factory=list)
    synthesis: str = ""
    explanation: Explanation | None = None
    decision_graph: DecisionGraph | None = None
    duration_ms: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
