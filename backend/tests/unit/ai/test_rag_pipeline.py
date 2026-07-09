import pytest

from tmis.ai.rag.chunking import FixedSizeChunker
from tmis.ai.rag.cleaning import WhitespaceNormalizingCleaner
from tmis.ai.rag.indexing import InMemoryVectorIndex
from tmis.ai.rag.ingestion import PlainTextIngestor
from tmis.ai.rag.pipeline import RagPipeline
from tmis.ai.rag.ports import RawDocument


def test_ingestor_wraps_content_into_raw_document() -> None:
    doc = PlainTextIngestor().ingest("id-1", "hello", {"lang": "fr"})
    assert doc == RawDocument(id="id-1", content="hello", metadata={"lang": "fr"})


def test_cleaner_collapses_whitespace() -> None:
    raw = RawDocument(id="1", content="hello   \n\n  world  ", metadata={})
    cleaned = WhitespaceNormalizingCleaner().clean(raw)
    assert cleaned.content == "hello world"


def test_chunker_produces_overlapping_windows() -> None:
    raw = RawDocument(id="doc", content="x" * 1000, metadata={})
    chunks = FixedSizeChunker(chunk_size=400, overlap=50).chunk(raw)
    assert chunks[0].id == "doc::0"
    assert len(chunks[0].content) == 400
    # Consecutive chunks share `overlap` characters.
    assert chunks[0].content[-50:] == chunks[1].content[:50]


def test_chunker_rejects_overlap_larger_than_chunk_size() -> None:
    with pytest.raises(ValueError):
        FixedSizeChunker(chunk_size=100, overlap=100)


def test_chunker_returns_empty_list_for_empty_document() -> None:
    raw = RawDocument(id="empty", content="", metadata={})
    assert FixedSizeChunker().chunk(raw) == []


@pytest.mark.asyncio
async def test_index_search_filters_by_metadata() -> None:
    from tmis.ai.rag.ports import Chunk

    index = InMemoryVectorIndex()
    chunk_a = Chunk(id="a", document_id="d1", content="a", metadata={"case_id": "1"})
    chunk_b = Chunk(id="b", document_id="d2", content="b", metadata={"case_id": "2"})
    await index.upsert([chunk_a, chunk_b], [[1.0, 0.0], [1.0, 0.0]])

    results = await index.search([1.0, 0.0], top_k=5, filters={"case_id": "1"})

    assert [r.chunk_id for r in results] == ["a"]


@pytest.mark.asyncio
async def test_rag_pipeline_ingest_and_query_end_to_end() -> None:
    pipeline = RagPipeline()
    await pipeline.ingest_document(
        "doc-1", "Le bailleur doit délivrer un logement décent au locataire."
    )
    await pipeline.ingest_document(
        "doc-2", "La responsabilité du fait des choses suppose la garde de la chose."
    )

    citations = await pipeline.query("logement décent locataire", top_k=1)

    assert len(citations) == 1
    assert citations[0].reference == "doc-1"
    assert citations[0].connector == "rag"


@pytest.mark.asyncio
async def test_rag_pipeline_ingest_empty_document_indexes_nothing() -> None:
    pipeline = RagPipeline()
    chunks = await pipeline.ingest_document("empty", "")
    assert chunks == []
