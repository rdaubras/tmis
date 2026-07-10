from typing import TYPE_CHECKING, Protocol

from tmis.ai.schemas.provider import ModelResponse
from tmis.case_intelligence.summaries.schemas import CaseSummary

if TYPE_CHECKING:
    from tmis.case_intelligence.cases.schemas import CaseProfile


class SummaryKernelPort(Protocol):
    """Everything a summary generator is allowed to use from the Kernel —
    deliberately narrow, mirroring `tmis.ai.langgraph.ports.KernelFacadePort`
    (see docs/11-langgraph-architecture.md), so no business logic ever
    imports a provider or connector directly.
    """

    async def complete(self, prompt: str) -> ModelResponse: ...


class SummaryGeneratorPort(Protocol):
    """Port implemented by every interchangeable case-summary generator."""

    async def generate(self, profile: "CaseProfile") -> CaseSummary: ...
