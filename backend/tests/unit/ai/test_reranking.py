from tmis.ai.reranking.simple_reranker import KeywordOverlapReranker
from tmis.ai.schemas.citation import RetrievedChunk


def test_exact_phrase_match_is_boosted_above_higher_scored_partial_match() -> None:
    reranker = KeywordOverlapReranker(exact_phrase_bonus=0.5)
    chunks = [
        RetrievedChunk(
            chunk_id="high-score",
            document_id="d1",
            content="unrelated but scored high",
            score=0.9,
            metadata={},
        ),
        RetrievedChunk(
            chunk_id="exact-match",
            document_id="d2",
            content="résiliation du contrat de bail",
            score=0.5,
            metadata={},
        ),
    ]

    result = reranker.rerank("résiliation du contrat de bail", chunks)

    assert result[0].chunk_id == "exact-match"


def test_rerank_preserves_order_when_no_phrase_matches() -> None:
    reranker = KeywordOverlapReranker()
    chunks = [
        RetrievedChunk(chunk_id="a", document_id="d1", content="alpha", score=0.8, metadata={}),
        RetrievedChunk(chunk_id="b", document_id="d2", content="beta", score=0.3, metadata={}),
    ]

    result = reranker.rerank("gamma", chunks)

    assert [c.chunk_id for c in result] == ["a", "b"]
