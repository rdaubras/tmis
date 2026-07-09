from tmis.ai.embeddings.similarity import cosine_similarity
from tmis.ai.rag.ports import Chunk
from tmis.ai.schemas.citation import RetrievedChunk


class InMemoryVectorIndex:
    """Implements `IndexPort` with brute-force cosine similarity search.

    Stands in for Qdrant (see docs/03-architecture-technique.md) until
    Sprint 7 wires the real vector database; the search semantics
    (payload filtering, top-k ranking) match what the real index will do.
    """

    def __init__(self) -> None:
        self._entries: list[tuple[Chunk, list[float]]] = []

    async def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")
        self._entries.extend(zip(chunks, vectors, strict=True))

    async def search(
        self, vector: list[float], *, top_k: int = 5, filters: dict[str, str] | None = None
    ) -> list[RetrievedChunk]:
        candidates = self._entries
        if filters:
            candidates = [
                (chunk, chunk_vector)
                for chunk, chunk_vector in candidates
                if all(chunk.metadata.get(k) == v for k, v in filters.items())
            ]
        scored = [
            RetrievedChunk(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                content=chunk.content,
                score=cosine_similarity(vector, chunk_vector),
                metadata=chunk.metadata,
            )
            for chunk, chunk_vector in candidates
        ]
        scored.sort(key=lambda c: c.score, reverse=True)
        return scored[:top_k]
