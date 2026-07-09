from typing import Protocol

from tmis.ai.schemas.citation import RetrievedChunk


class RerankerPort(Protocol):
    def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]: ...
