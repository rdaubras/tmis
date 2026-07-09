from tmis.ai.embeddings.hashing_provider import HashingEmbeddingProvider
from tmis.ai.embeddings.ports import EmbeddingProviderPort
from tmis.ai.rag.chunking import FixedSizeChunker
from tmis.ai.rag.cleaning import WhitespaceNormalizingCleaner
from tmis.ai.rag.indexing import InMemoryVectorIndex
from tmis.ai.rag.ingestion import PlainTextIngestor
from tmis.ai.rag.ports import Chunk, ChunkerPort, CleanerPort, IndexPort, IngestorPort
from tmis.ai.reranking.ports import RerankerPort
from tmis.ai.reranking.simple_reranker import KeywordOverlapReranker
from tmis.ai.retrieval.hybrid_retriever import HybridRetriever
from tmis.ai.retrieval.ports import RetrieverPort
from tmis.ai.schemas.citation import Citation


class RagPipeline:
    """Wires the full pipeline described in docs/06-strategie-rag.md:
    ingestion -> cleaning -> chunking -> embeddings -> indexing on the
    write side, retrieval -> reranking -> citations on the read side.

    Every stage is injected as a port, so a future sprint can swap the
    in-memory index for Qdrant, or the hashing embedding provider for a
    real model, without touching this class.
    """

    def __init__(
        self,
        *,
        ingestor: IngestorPort | None = None,
        cleaner: CleanerPort | None = None,
        chunker: ChunkerPort | None = None,
        embedding_provider: EmbeddingProviderPort | None = None,
        index: IndexPort | None = None,
        retriever: RetrieverPort | None = None,
        reranker: RerankerPort | None = None,
    ) -> None:
        self._ingestor = ingestor or PlainTextIngestor()
        self._cleaner = cleaner or WhitespaceNormalizingCleaner()
        self._chunker = chunker or FixedSizeChunker()
        self._embedding_provider = embedding_provider or HashingEmbeddingProvider()
        self._index = index or InMemoryVectorIndex()
        self._retriever = retriever or HybridRetriever(self._index, self._embedding_provider)
        self._reranker = reranker or KeywordOverlapReranker()

    async def ingest_document(
        self, raw_id: str, content: str, metadata: dict[str, str] | None = None
    ) -> list[Chunk]:
        raw = self._ingestor.ingest(raw_id, content, metadata)
        cleaned = self._cleaner.clean(raw)
        chunks = self._chunker.chunk(cleaned)
        if not chunks:
            return []
        vectors = await self._embedding_provider.embed([chunk.content for chunk in chunks])
        await self._index.upsert(chunks, vectors)
        return chunks

    async def query(
        self, query: str, *, top_k: int = 5, filters: dict[str, str] | None = None
    ) -> list[Citation]:
        candidates = await self._retriever.retrieve(
            query, top_k=top_k * 2, filters=filters
        )
        reranked = self._reranker.rerank(query, candidates)[:top_k]
        return [
            chunk.to_citation(connector="rag", reference=chunk.document_id)
            for chunk in reranked
        ]
