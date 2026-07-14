import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("TMIS_RUN_MODEL_DOWNLOAD_TESTS"),
    reason="Downloads a real sentence-transformers model from the Hugging Face Hub; "
    "opt in with TMIS_RUN_MODEL_DOWNLOAD_TESTS=1 on a machine with network access "
    "(mirrors the TMIS_REDIS_URL-gated tests in test_redis_backends.py).",
)


@pytest.mark.asyncio
async def test_real_model_produces_similar_vectors_for_similar_french_sentences() -> None:
    from tmis.ai.embeddings.adapters.sentence_transformer_provider import (
        SentenceTransformerEmbeddingProvider,
    )
    from tmis.ai.embeddings.similarity import cosine_similarity

    provider = SentenceTransformerEmbeddingProvider("paraphrase-multilingual-MiniLM-L12-v2")
    [bail, bail_variant, unrelated] = await provider.embed(
        [
            "Le bailleur doit délivrer un logement décent au locataire.",
            "Le propriétaire est tenu de fournir un logement décent au locataire.",
            "La recette de la tarte aux pommes nécessite quatre pommes.",
        ]
    )

    assert cosine_similarity(bail, bail_variant) > cosine_similarity(bail, unrelated)
    assert provider.dimensions == len(bail)
