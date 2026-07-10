from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

from tmis.case_intelligence.facts.schemas import Fact
from tmis.legal_drafting.citations.schemas import DraftCitation
from tmis.legal_drafting.review.schemas import ReviewFinding
from tmis.legal_drafting.sections.schemas import Section
from tmis.legal_drafting.style.schemas import StyleProfile
from tmis.legal_drafting.templates.schemas import DocumentType
from tmis.legal_reasoning.reasoner.schemas import ReasoningSession
from tmis.legal_research.search.schemas import ResearchResult


class DraftWorkflowStatus(str, Enum):
    """The internal review workflow a draft goes through — entirely
    separate from `Document.is_draft`, which never changes. Even
    `LAWYER_APPROVED` only means the avocat internally signed off on the
    draft's content inside TMIS; it is not a legal act and does not make
    the document anything other than a draft (see
    docs/28-legal-drafting.md — Human In The Loop)."""

    GENERATED = "generated"
    UNDER_REVIEW = "under_review"
    LAWYER_APPROVED = "lawyer_approved"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class DraftingContext:
    """Everything the orchestrator gathered in its "analyse du contexte"
    step, bundled for internal use only — no other module's port takes
    this object directly, they take the individual pieces (see
    docs/28-legal-drafting.md — Document Orchestrator)."""

    case_id: str | None
    facts: list[Fact]
    research_results: list[ResearchResult]
    reasoning_session: ReasoningSession | None
    style_profile: StyleProfile
    variables: dict[str, str] = field(default_factory=dict)


@dataclass
class Document:
    """A draft document — the Legal Drafting Studio's output. Every
    document TMIS produces stays a draft: `is_draft` is a read-only
    property that always returns `True`, on purpose, so no code path
    anywhere can ever flip it (see docs/28-legal-drafting.md)."""

    id: str
    template_id: str
    document_type: DocumentType
    case_id: str | None
    title: str
    sections: list[Section] = field(default_factory=list)
    citations: list[DraftCitation] = field(default_factory=list)
    review_findings: list[ReviewFinding] = field(default_factory=list)
    status: DraftWorkflowStatus = DraftWorkflowStatus.GENERATED
    # Remembered so that regenerating a section/paragraph later can
    # rebuild the exact same drafting context (facts, research results,
    # reasoning session, style, template variables) without the caller
    # having to resupply everything.
    source_question: str | None = None
    reasoning_session_id: str | None = None
    style_profile_id: str = "default"
    variables: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_draft(self) -> bool:
        """Always `True` — TMIS never presents a document as legally
        validated (see the Sprint 7 constraint in
        docs/09-roadmap-30-sprints.md)."""
        return True
