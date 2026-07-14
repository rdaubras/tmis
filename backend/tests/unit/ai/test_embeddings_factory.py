import pytest

from tmis.ai.embeddings import factory
from tmis.ai.embeddings.adapters.sentence_transformer_provider import (
    SentenceTransformerEmbeddingProvider,
)
from tmis.ai.embeddings.hashing_provider import HashingEmbeddingProvider
from tmis.core.config import Settings


def test_defaults_to_hashing_provider_with_no_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory, "get_settings", lambda: Settings())

    provider = factory.get_embedding_provider()

    assert isinstance(provider, HashingEmbeddingProvider)


def test_selects_sentence_transformers_when_configured_and_loadable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        factory, "get_settings", lambda: Settings(embedding_backend="sentence_transformers")
    )

    class _StubProvider:
        embedding_name = "stub"
        dimensions = 4

        def __init__(self, model_name: str) -> None:
            self.model_name = model_name

        async def embed(self, texts: list[str]) -> list[list[float]]:
            return [[0.0] * 4 for _ in texts]

    monkeypatch.setattr(factory, "SentenceTransformerEmbeddingProvider", _StubProvider)

    provider = factory.get_embedding_provider()

    assert isinstance(provider, _StubProvider)


def test_falls_back_to_hashing_when_the_real_model_fails_to_load(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        factory, "get_settings", lambda: Settings(embedding_backend="sentence_transformers")
    )

    def _raise(model_name: str) -> SentenceTransformerEmbeddingProvider:
        raise OSError("no network to download the model")

    monkeypatch.setattr(factory, "SentenceTransformerEmbeddingProvider", _raise)

    provider = factory.get_embedding_provider()

    assert isinstance(provider, HashingEmbeddingProvider)
