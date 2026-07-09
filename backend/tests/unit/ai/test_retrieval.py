import pytest

from tmis.ai.embeddings.hashing_provider import HashingEmbeddingProvider
from tmis.ai.retrieval.hybrid_retriever import HybridRetriever
from tmis.ai.schemas.citation import RetrievedChunk


class _FakeIndex:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self._chunks = chunks

    async def upsert(self, chunks, vectors) -> None:  # pragma: no cover - unused in this test
        raise NotImplementedError

    async def search(
        self, vector: list[float], *, top_k: int = 5, filters: dict[str, str] | None = None
    ) -> list[RetrievedChunk]:
        # Return every fixture chunk with a flat vector score; the retriever
        # is expected to blend this with lexical overlap.
        return [
            RetrievedChunk(
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                content=c.content,
                score=0.5,
                metadata=c.metadata,
            )
            for c in self._chunks
        ][:top_k]


@pytest.mark.asyncio
async def test_hybrid_retriever_ranks_lexically_matching_chunk_first() -> None:
    chunks = [
        RetrievedChunk(
            chunk_id="a",
            document_id="d1",
            content="contrat de bail commercial",
            score=0,
            metadata={},
        ),
        RetrievedChunk(
            chunk_id="b",
            document_id="d2",
            content="recette de cuisine italienne",
            score=0,
            metadata={},
        ),
    ]
    retriever = HybridRetriever(_FakeIndex(chunks), HashingEmbeddingProvider())

    results = await retriever.retrieve("contrat de bail", top_k=2)

    assert results[0].chunk_id == "a"


@pytest.mark.asyncio
async def test_hybrid_retriever_respects_top_k() -> None:
    chunks = [
        RetrievedChunk(chunk_id=str(i), document_id="d", content=f"texte {i}", score=0, metadata={})
        for i in range(5)
    ]
    retriever = HybridRetriever(_FakeIndex(chunks), HashingEmbeddingProvider())

    results = await retriever.retrieve("texte", top_k=2)

    assert len(results) == 2
