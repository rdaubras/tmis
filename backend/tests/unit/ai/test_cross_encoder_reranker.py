from typing import Any

import numpy as np
import pytest
import sentence_transformers

from tmis.ai.reranking.adapters.cross_encoder_reranker import CrossEncoderReranker
from tmis.ai.schemas.citation import RetrievedChunk


class _FakeCrossEncoder:
    """Scores each `(query, content)` pair by lexical overlap — deterministic
    and dependency-free, standing in for a real transformer model."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def predict(self, pairs: list[tuple[str, str]], **kwargs: Any) -> np.ndarray:
        scores = []
        for query, content in pairs:
            query_tokens = set(query.lower().split())
            content_tokens = set(content.lower().split())
            scores.append(float(len(query_tokens & content_tokens)))
        return np.array(scores)


def test_rerank_orders_chunks_by_the_model_score(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sentence_transformers, "CrossEncoder", _FakeCrossEncoder)
    reranker = CrossEncoderReranker("fake-cross-encoder")

    chunks = [
        RetrievedChunk(
            chunk_id="low", document_id="d1", content="unrelated text", score=0.9, metadata={}
        ),
        RetrievedChunk(
            chunk_id="high",
            document_id="d2",
            content="résiliation du contrat de bail",
            score=0.1,
            metadata={},
        ),
    ]

    result = reranker.rerank("résiliation contrat bail", chunks)

    assert [c.chunk_id for c in result] == ["high", "low"]


def test_rerank_replaces_the_original_score_with_the_model_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sentence_transformers, "CrossEncoder", _FakeCrossEncoder)
    reranker = CrossEncoderReranker("fake-cross-encoder")

    chunks = [
        RetrievedChunk(
            chunk_id="a", document_id="d1", content="alpha beta", score=0.5, metadata={}
        ),
    ]

    [result] = reranker.rerank("alpha", chunks)

    assert result.score == 1.0


def test_rerank_returns_empty_list_for_no_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sentence_transformers, "CrossEncoder", _FakeCrossEncoder)
    reranker = CrossEncoderReranker("fake-cross-encoder")

    assert reranker.rerank("query", []) == []
