import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, kw_only=True)
class Event:
    """Base class for every event exchanged on the `EventBus`."""

    workflow_id: uuid.UUID
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def event_type(self) -> str:
        return type(self).__name__


@dataclass(frozen=True, kw_only=True)
class UserQuestionReceived(Event):
    question: str


@dataclass(frozen=True, kw_only=True)
class WorkflowStarted(Event):
    workflow_name: str


@dataclass(frozen=True, kw_only=True)
class ResearchCompleted(Event):
    result_count: int


@dataclass(frozen=True, kw_only=True)
class DraftGenerated(Event):
    draft_id: str


@dataclass(frozen=True, kw_only=True)
class VerificationCompleted(Event):
    warning_count: int


@dataclass(frozen=True, kw_only=True)
class WorkflowFinished(Event):
    workflow_name: str
    success: bool


# ---------------------------------------------------------------------
# Document Intelligence Engine events (Sprint 3, see
# docs/14-document-intelligence.md). `workflow_id` correlates every event
# of a single document processing run; `document_id` identifies the
# document across runs.
# ---------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class DocumentUploaded(Event):
    document_id: str
    filename: str
    case_id: str | None = None


@dataclass(frozen=True, kw_only=True)
class OCRCompleted(Event):
    document_id: str
    confidence: float


@dataclass(frozen=True, kw_only=True)
class LayoutDetected(Event):
    document_id: str
    block_count: int


@dataclass(frozen=True, kw_only=True)
class MetadataExtracted(Event):
    document_id: str


@dataclass(frozen=True, kw_only=True)
class EntitiesExtracted(Event):
    document_id: str
    entity_count: int


@dataclass(frozen=True, kw_only=True)
class TimelineBuilt(Event):
    document_id: str
    event_count: int


@dataclass(frozen=True, kw_only=True)
class EmbeddingsCreated(Event):
    document_id: str
    chunk_count: int


@dataclass(frozen=True, kw_only=True)
class KnowledgeUpdated(Event):
    document_id: str
    node_count: int


@dataclass(frozen=True, kw_only=True)
class DocumentProcessed(Event):
    document_id: str
    success: bool
    case_id: str | None = None
    # Optional (`document_intelligence` is not itself firm-isolated yet —
    # see docs/19-case-intelligence.md, "case_intelligence" persistent &
    # isolated slice, out-of-scope note): carried through, when the
    # caller has it, purely so `case_intelligence`'s own event handler
    # (ADR-CASEINT-01) can scope the resulting case enrichment to the
    # right cabinet instead of trusting `case_id` as a bare, unverified
    # string.
    firm_id: str | None = None


# ---------------------------------------------------------------------
# Case Intelligence Engine events (Sprint 4, see
# docs/19-case-intelligence.md). `workflow_id` correlates every event of a
# single case-enrichment run; `case_id` identifies the case across runs.
# ---------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class CaseCreated(Event):
    case_id: str


@dataclass(frozen=True, kw_only=True)
class CaseUpdated(Event):
    case_id: str
    document_id: str


@dataclass(frozen=True, kw_only=True)
class FactsUpdated(Event):
    case_id: str
    fact_count: int


@dataclass(frozen=True, kw_only=True)
class TimelineUpdated(Event):
    case_id: str
    entry_count: int
    inconsistency_count: int


@dataclass(frozen=True, kw_only=True)
class EvidenceUpdated(Event):
    case_id: str
    evidence_link_count: int


@dataclass(frozen=True, kw_only=True)
class IssueDetected(Event):
    case_id: str
    issue_count: int


@dataclass(frozen=True, kw_only=True)
class CaseIndexed(Event):
    case_id: str


@dataclass(frozen=True, kw_only=True)
class CaseSummarized(Event):
    case_id: str


# ---------------------------------------------------------------------
# Legal Reasoning Engine events (Sprint 6, see
# docs/25-legal-reasoning.md). `workflow_id` correlates every event of a
# single reasoning run; `session_id` identifies the `ReasoningSession`.
# ---------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class ReasoningStarted(Event):
    session_id: str
    question: str
    case_id: str | None = None


@dataclass(frozen=True, kw_only=True)
class HypothesisCreated(Event):
    session_id: str
    hypothesis_id: str


@dataclass(frozen=True, kw_only=True)
class ArgumentAdded(Event):
    session_id: str
    argument_id: str
    hypothesis_id: str


@dataclass(frozen=True, kw_only=True)
class CounterArgumentAdded(Event):
    session_id: str
    counter_argument_id: str
    argument_id: str


@dataclass(frozen=True, kw_only=True)
class ConflictDetected(Event):
    session_id: str
    conflict_id: str
    conflict_type: str


@dataclass(frozen=True, kw_only=True)
class ConfidenceCalculated(Event):
    session_id: str
    hypothesis_id: str
    value: float


@dataclass(frozen=True, kw_only=True)
class ReasoningCompleted(Event):
    session_id: str
    hypothesis_count: int
    conflict_count: int
    duration_ms: float
