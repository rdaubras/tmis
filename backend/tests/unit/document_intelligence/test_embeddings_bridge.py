import pytest

from tmis.ai.rag.ports import Chunk
from tmis.document_intelligence.embeddings.bridge import DocumentEmbeddingBridge


@pytest.mark.asyncio
async def test_embed_and_index_returns_one_vector_per_chunk() -> None:
    bridge = DocumentEmbeddingBridge()
    chunks = [
        Chunk(id="doc-1::0", document_id="doc-1", content="contrat de bail", metadata={}),
        Chunk(id="doc-1::1", document_id="doc-1", content="résiliation anticipée", metadata={}),
    ]

    vectors = await bridge.embed_and_index(chunks)

    assert len(vectors) == 2


@pytest.mark.asyncio
async def test_embed_and_index_with_no_chunks_returns_empty_list() -> None:
    assert await DocumentEmbeddingBridge().embed_and_index([]) == []


@pytest.mark.asyncio
async def test_search_finds_the_matching_chunk() -> None:
    bridge = DocumentEmbeddingBridge()
    chunks = [
        Chunk(
            id="doc-1::0",
            document_id="doc-1",
            content="contrat de bail commercial",
            metadata={},
        ),
        Chunk(
            id="doc-1::1",
            document_id="doc-1",
            content="recette de cuisine italienne",
            metadata={},
        ),
    ]
    await bridge.embed_and_index(chunks)

    results = await bridge.search("bail commercial", top_k=1)

    assert results[0].chunk_id == "doc-1::0"
