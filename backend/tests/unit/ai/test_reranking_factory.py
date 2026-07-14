import pytest

from tmis.ai.reranking import factory
from tmis.ai.reranking.simple_reranker import KeywordOverlapReranker
from tmis.core.config import Settings


def test_defaults_to_keyword_overlap_reranker_with_no_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(factory, "get_settings", lambda: Settings())

    reranker = factory.get_reranker()

    assert isinstance(reranker, KeywordOverlapReranker)


def test_selects_cross_encoder_when_configured_and_loadable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        factory, "get_settings", lambda: Settings(reranker_backend="cross_encoder")
    )

    class _StubReranker:
        def __init__(self, model_name: str) -> None:
            self.model_name = model_name

        def rerank(self, query: str, chunks: list[object]) -> list[object]:
            return chunks

    monkeypatch.setattr(
        "tmis.ai.reranking.adapters.cross_encoder_reranker.CrossEncoderReranker",
        _StubReranker,
    )

    reranker = factory.get_reranker()

    assert isinstance(reranker, _StubReranker)
    assert reranker.model_name == "cross-encoder/ms-marco-MiniLM-L-6-v2"


def test_falls_back_to_keyword_overlap_when_the_cross_encoder_model_fails_to_load(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        factory, "get_settings", lambda: Settings(reranker_backend="cross_encoder")
    )

    def _raise(model_name: str) -> None:
        raise OSError("no network to download the model")

    monkeypatch.setattr(
        "tmis.ai.reranking.adapters.cross_encoder_reranker.CrossEncoderReranker", _raise
    )

    reranker = factory.get_reranker()

    assert isinstance(reranker, KeywordOverlapReranker)
