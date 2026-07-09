import pytest

from tmis.ai.embeddings.hashing_provider import HashingEmbeddingProvider
from tmis.ai.embeddings.similarity import cosine_similarity


@pytest.mark.asyncio
async def test_embed_returns_one_vector_per_text_with_configured_dimensions() -> None:
    provider = HashingEmbeddingProvider(dimensions=32)
    vectors = await provider.embed(["bonjour le monde", "autre texte"])
    assert len(vectors) == 2
    assert all(len(v) == 32 for v in vectors)


@pytest.mark.asyncio
async def test_embed_is_deterministic() -> None:
    provider = HashingEmbeddingProvider()
    [v1] = await provider.embed(["même texte"])
    [v2] = await provider.embed(["même texte"])
    assert v1 == v2


@pytest.mark.asyncio
async def test_identical_texts_have_similarity_one() -> None:
    provider = HashingEmbeddingProvider()
    [v1, v2] = await provider.embed(["le contrat de bail", "le contrat de bail"])
    assert cosine_similarity(v1, v2) == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_unrelated_texts_have_lower_similarity_than_identical_ones() -> None:
    provider = HashingEmbeddingProvider()
    [base, same, different] = await provider.embed(
        ["résiliation du contrat de bail", "résiliation du contrat de bail", "recette de cuisine"]
    )
    assert cosine_similarity(base, same) > cosine_similarity(base, different)


def test_cosine_similarity_of_empty_vectors_is_zero() -> None:
    assert cosine_similarity([], []) == 0.0
