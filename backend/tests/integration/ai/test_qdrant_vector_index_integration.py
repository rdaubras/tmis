"""Integration test for `QdrantVectorIndex` against a real Qdrant engine.

No Docker daemon is available in this environment (confirmed: no other
test in this repo uses testcontainers), so this exercises `qdrant-client`'s
built-in local-mode engine (`AsyncQdrantClient(location=":memory:")`) —
the same Rust core Qdrant runs in production, embedded rather than reached
over the wire. This is the closest available equivalent to the aiosqlite
pattern the Sprint 26 SQLAlchemy store tests use for the same reason (a
real engine, no external service to stand up). See
docs/reports/sprint-27-rapport-audit.md for why testcontainers itself
isn't used.
"""

import pytest
from qdrant_client import AsyncQdrantClient

from tmis.ai.rag.adapters.qdrant_index import QdrantVectorIndex
from tmis.ai.rag.ports import Chunk


@pytest.fixture
def index() -> QdrantVectorIndex:
    client = AsyncQdrantClient(location=":memory:")
    return QdrantVectorIndex(client, collection_name="tmis_rag_chunks_test", dimensions=3)


@pytest.mark.asyncio
async def test_upsert_then_search_returns_the_closest_chunk_first(
    index: QdrantVectorIndex,
) -> None:
    chunk_a = Chunk(id="a", document_id="d1", content="le bailleur", metadata={"case_id": "1"})
    chunk_b = Chunk(id="b", document_id="d2", content="la garde", metadata={"case_id": "2"})

    await index.upsert([chunk_a, chunk_b], [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    results = await index.search([1.0, 0.0, 0.0], top_k=5)

    assert results[0].chunk_id == "a"
    assert results[0].document_id == "d1"
    assert results[0].content == "le bailleur"


@pytest.mark.asyncio
async def test_search_filters_by_metadata(index: QdrantVectorIndex) -> None:
    chunk_a = Chunk(id="a", document_id="d1", content="a", metadata={"case_id": "1"})
    chunk_b = Chunk(id="b", document_id="d2", content="b", metadata={"case_id": "2"})
    await index.upsert([chunk_a, chunk_b], [[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]])

    results = await index.search([1.0, 0.0, 0.0], top_k=5, filters={"case_id": "2"})

    assert [r.chunk_id for r in results] == ["b"]


@pytest.mark.asyncio
async def test_upsert_is_idempotent_per_chunk_id(index: QdrantVectorIndex) -> None:
    chunk = Chunk(id="a", document_id="d1", content="v1", metadata={})
    await index.upsert([chunk], [[1.0, 0.0, 0.0]])

    updated_chunk = Chunk(id="a", document_id="d1", content="v2", metadata={})
    await index.upsert([updated_chunk], [[1.0, 0.0, 0.0]])

    results = await index.search([1.0, 0.0, 0.0], top_k=10)
    assert len(results) == 1
    assert results[0].content == "v2"


@pytest.mark.asyncio
async def test_upsert_rejects_mismatched_chunks_and_vectors(index: QdrantVectorIndex) -> None:
    chunk = Chunk(id="a", document_id="d1", content="a", metadata={})
    with pytest.raises(ValueError, match="same length"):
        await index.upsert([chunk], [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])


@pytest.mark.asyncio
async def test_upsert_with_empty_chunks_is_a_no_op(index: QdrantVectorIndex) -> None:
    await index.upsert([], [])
    results = await index.search([1.0, 0.0, 0.0], top_k=5)
    assert results == []
