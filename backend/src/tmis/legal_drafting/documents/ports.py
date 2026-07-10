from typing import Protocol

from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.legal_drafting.documents.schemas import Document
from tmis.legal_reasoning.reasoner.schemas import ReasoningSession
from tmis.legal_research.search.schemas import ResearchResponse


class DocumentStorePort(Protocol):
    """Port implemented by every interchangeable draft store."""

    def get(self, document_id: str) -> Document | None: ...

    def save(self, document: Document) -> None: ...

    def list_ids(self) -> list[str]: ...


class DraftingCasePort(Protocol):
    """Narrow read access to the Case Intelligence Engine (Sprint 4) —
    the LDS never re-implements case analysis."""

    def get_profile(self, case_id: str) -> CaseProfile | None: ...


class DraftingResearchPort(Protocol):
    """Narrow read access to the Legal Research Engine (Sprint 5) — the
    LDS never queries a connector itself."""

    async def search(self, query: str, *, case_id: str | None = None) -> ResearchResponse: ...


class DraftingReasoningPort(Protocol):
    """Narrow read/trigger access to the Legal Reasoning Engine
    (Sprint 6) — the LDS never builds hypotheses, arguments or
    confidence scores itself; it only turns an existing (or freshly
    triggered) `ReasoningSession` into a draft."""

    async def reason(self, question: str, *, case_id: str | None = None) -> ReasoningSession: ...

    def get_session(self, session_id: str) -> ReasoningSession | None: ...
