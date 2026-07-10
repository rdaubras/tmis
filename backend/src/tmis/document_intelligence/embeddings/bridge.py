from tmis.ai.embeddings.hashing_provider import HashingEmbeddingProvider
from tmis.ai.embeddings.ports import EmbeddingProviderPort
from tmis.ai.rag.indexing import InMemoryVectorIndex
from tmis.ai.rag.ports import Chunk, IndexPort
from tmis.ai.schemas.citation import RetrievedChunk


class DocumentEmbeddingBridge:
    """Wires document chunks into the Sprint 2 embeddings/RAG modules:

    Chunk -> `EmbeddingProviderPort.embed()` -> `IndexPort.upsert()`

    Any `EmbeddingProviderPort` implementation works here — including a
    real model provider wired in a future sprint — without this class
    changing (see docs/14-document-intelligence.md).
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProviderPort | None = None,
        index: IndexPort | None = None,
    ) -> None:
        self.embedding_provider = embedding_provider or HashingEmbeddingProvider()
        self.index = index or InMemoryVectorIndex()

    async def embed_and_index(self, chunks: list[Chunk]) -> list[list[float]]:
        if not chunks:
            return []
        vectors = await self.embedding_provider.embed([chunk.content for chunk in chunks])
        await self.index.upsert(chunks, vectors)
        return vectors

    async def search(
        self, query: str, *, top_k: int = 5, filters: dict[str, str] | None = None
    ) -> list[RetrievedChunk]:
        [query_vector] = await self.embedding_provider.embed([query])
        return await self.index.search(query_vector, top_k=top_k, filters=filters)
