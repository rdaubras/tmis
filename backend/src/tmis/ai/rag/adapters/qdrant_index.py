import uuid

from qdrant_client import AsyncQdrantClient
from qdrant_client import models as qmodels

from tmis.ai.rag.ports import Chunk
from tmis.ai.schemas.citation import RetrievedChunk


def _point_id(chunk_id: str) -> str:
    """Qdrant point ids must be an unsigned int or a UUID; chunk ids are
    free-form strings (e.g. `"doc-1::0"`), so derive a stable UUID5 from
    them — the same `chunk_id` always maps to the same point, making
    `upsert` idempotent exactly like `InMemoryVectorIndex` appending a
    `(chunk, vector)` pair is not (see the fallback test asserting a
    re-upserted chunk overwrites rather than duplicates)."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))


class QdrantVectorIndex:
    """Implements `IndexPort` against a real Qdrant collection (see
    docs/03-architecture-technique.md, which already names Qdrant as the
    RAG target, and docs/153-architecture-rag-production.md for how this
    adapter is selected over `InMemoryVectorIndex`).

    Chunk metadata is stored as the point payload alongside content and
    document id, so `search(..., filters=...)` maps onto Qdrant payload
    filtering with the same semantics `InMemoryVectorIndex` implements in
    brute force (a single shared collection, strict per-key equality
    filtering — see docs/03, "Isolation multi-tenant dans Qdrant").
    """

    def __init__(
        self,
        client: AsyncQdrantClient,
        *,
        collection_name: str,
        dimensions: int,
    ) -> None:
        self._client = client
        self._collection_name = collection_name
        self._dimensions = dimensions
        self._collection_ready = False

    async def _ensure_collection(self) -> None:
        if self._collection_ready:
            return
        if not await self._client.collection_exists(self._collection_name):
            await self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=qmodels.VectorParams(
                    size=self._dimensions, distance=qmodels.Distance.COSINE
                ),
            )
        self._collection_ready = True

    async def upsert(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")
        if not chunks:
            return
        await self._ensure_collection()
        points = [
            qmodels.PointStruct(
                id=_point_id(chunk.id),
                vector=vector,
                payload={
                    "chunk_id": chunk.id,
                    "document_id": chunk.document_id,
                    "content": chunk.content,
                    "metadata": chunk.metadata,
                },
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        await self._client.upsert(collection_name=self._collection_name, points=points)

    async def search(
        self, vector: list[float], *, top_k: int = 5, filters: dict[str, str] | None = None
    ) -> list[RetrievedChunk]:
        await self._ensure_collection()
        query_filter = None
        if filters:
            query_filter = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key=f"metadata.{key}", match=qmodels.MatchValue(value=value)
                    )
                    for key, value in filters.items()
                ]
            )
        response = await self._client.query_points(
            collection_name=self._collection_name,
            query=vector,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )
        return [
            RetrievedChunk(
                chunk_id=point.payload["chunk_id"],
                document_id=point.payload["document_id"],
                content=point.payload["content"],
                score=point.score,
                metadata=point.payload.get("metadata", {}),
            )
            for point in response.points
            if point.payload is not None
        ]
