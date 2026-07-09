from dataclasses import dataclass, field
from typing import Protocol

from tmis.ai.schemas.citation import RetrievedChunk


@dataclass(frozen=True, slots=True)
class RawDocument:
    id: str
    content: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Chunk:
    id: str
    document_id: str
    content: str
    metadata: dict[str, str] = field(default_factory=dict)


class IngestorPort(Protocol):
    def ingest(
        self, raw_id: str, content: str, metadata: dict[str, str] | None = None
    ) -> RawDocument: ...


class CleanerPort(Protocol):
    def clean(self, document: RawDocument) -> RawDocument: ...


class ChunkerPort(Protocol):
    def chunk(self, document: RawDocument) -> list[Chunk]: ...


class IndexPort(Protocol):
    async def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> None: ...

    async def search(
        self, vector: list[float], *, top_k: int = 5, filters: dict[str, str] | None = None
    ) -> list[RetrievedChunk]: ...
