import pytest

from tmis.ai.rag import factory
from tmis.ai.rag.adapters.qdrant_index import QdrantVectorIndex
from tmis.ai.rag.indexing import InMemoryVectorIndex
from tmis.core.config import Settings


def test_defaults_to_in_memory_index_with_no_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory, "get_settings", lambda: Settings())

    index = factory.get_vector_index(dimensions=64)

    assert isinstance(index, InMemoryVectorIndex)


def test_selects_qdrant_index_when_backend_is_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        factory, "get_settings", lambda: Settings(rag_vector_index_backend="qdrant")
    )

    index = factory.get_vector_index(dimensions=64)

    assert isinstance(index, QdrantVectorIndex)
