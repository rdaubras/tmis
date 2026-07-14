from typing import Protocol

from tmis.ai.schemas.provider import ModelResponse
from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.legal_reasoning.reasoner.schemas import ReasoningSession
from tmis.legal_research.search.schemas import ResearchResponse


class ReasoningKernelPort(Protocol):
    """Everything the Legal Reasoning Engine is allowed to use from the
    Kernel — deliberately narrow, mirroring
    `tmis.case_intelligence.summaries.ports.SummaryKernelPort`: the only
    LLM call point in the whole engine is the final synthesis (see
    docs/25-legal-reasoning.md)."""

    async def complete(self, prompt: str) -> ModelResponse: ...


class ReasoningCasePort(Protocol):
    """Narrow read access to the Case Intelligence Engine's `CaseProfile`
    (facts, timeline inconsistencies) — the LRE² never re-implements case
    analysis, it consumes what the CIE (Sprint 4) already produced."""

    def get_profile(self, case_id: str) -> CaseProfile | None: ...


class ReasoningResearchPort(Protocol):
    """Narrow read access to the Legal Research Engine — the LRE² never
    queries a connector itself, it consumes `ResearchOrchestrator.search()`
    (Sprint 5)."""

    async def search(
        self, query: str, *, case_id: str | None = None
    ) -> ResearchResponse: ...


class SessionStorePort(Protocol):
    """Port implemented by every interchangeable `ReasoningSession` store
    (added in Sprint 26 — Module Document + Persistance — mirroring the
    `DocumentStorePort`/`CaseStorePort` shape from Sprints 3-4). Purely
    additive: no earlier port's signature changes, and
    `ReasoningOrchestrator` behaves exactly as before when none is
    supplied — see its docstring."""

    def get(self, session_id: str) -> ReasoningSession | None: ...

    def save(self, session: ReasoningSession) -> None: ...

    def list_ids(self) -> list[str]: ...
