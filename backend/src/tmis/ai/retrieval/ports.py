from typing import Protocol

from tmis.ai.schemas.citation import RetrievedChunk


class RetrieverPort(Protocol):
    async def retrieve(
        self, query: str, *, top_k: int = 5, filters: dict[str, str] | None = None
    ) -> list[RetrievedChunk]: ...
