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
