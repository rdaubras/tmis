from typing import Any

import numpy as np
import pytest
import sentence_transformers

from tmis.ai.embeddings.adapters.sentence_transformer_provider import (
    SentenceTransformerEmbeddingProvider,
)


class _FakeSentenceTransformer:
    def __init__(self, model_name: str, *, dimensions: int | None = 8) -> None:
        self.model_name = model_name
        self._dimensions = dimensions

    def get_sentence_embedding_dimension(self) -> int | None:
        return self._dimensions

    def encode(self, texts: list[str], **kwargs: Any) -> np.ndarray:
        return np.array([[float(len(text))] * (self._dimensions or 1) for text in texts])


@pytest.mark.asyncio
async def test_provider_reads_dimensions_from_the_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sentence_transformers, "SentenceTransformer", lambda name: _FakeSentenceTransformer(name)
    )

    provider = SentenceTransformerEmbeddingProvider("fake-model")

    assert provider.dimensions == 8
    assert provider.embedding_name == "sentence-transformers:fake-model"


@pytest.mark.asyncio
async def test_embed_returns_one_vector_per_text(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sentence_transformers, "SentenceTransformer", lambda name: _FakeSentenceTransformer(name)
    )

    provider = SentenceTransformerEmbeddingProvider("fake-model")
    vectors = await provider.embed(["a", "bb"])

    assert len(vectors) == 2
    assert all(len(v) == 8 for v in vectors)


def test_provider_raises_if_model_reports_no_dimensions(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sentence_transformers,
        "SentenceTransformer",
        lambda name: _FakeSentenceTransformer(name, dimensions=None),
    )

    with pytest.raises(RuntimeError, match="dimensions"):
        SentenceTransformerEmbeddingProvider("fake-model")
