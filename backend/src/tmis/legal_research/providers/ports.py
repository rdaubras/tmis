from typing import Protocol

from tmis.ai.schemas.connector import ConnectorDocument


class ResearchKernelPort(Protocol):
    """Everything the Legal Research Engine is allowed to use from the
    Kernel — deliberately narrow, mirroring
    `tmis.case_intelligence.summaries.ports.SummaryKernelPort`, so no LRE
    module ever imports a provider or connector directly (see
    docs/21-legal-research.md).
    """

    async def embed(self, texts: list[str]) -> list[list[float]]: ...

    async def search_connectors(
        self,
        query: str,
        *,
        connector_names: list[str] | None = None,
        filters: dict[str, object] | None = None,
        use_cache: bool = True,
    ) -> list[ConnectorDocument]: ...
