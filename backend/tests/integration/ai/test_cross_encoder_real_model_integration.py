import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("TMIS_RUN_MODEL_DOWNLOAD_TESTS"),
    reason="Downloads a real cross-encoder model from the Hugging Face Hub; "
    "opt in with TMIS_RUN_MODEL_DOWNLOAD_TESTS=1 on a machine with network access "
    "(mirrors test_sentence_transformer_real_model_integration.py).",
)


def test_real_cross_encoder_scores_a_relevant_chunk_above_an_unrelated_one() -> None:
    from tmis.ai.reranking.adapters.cross_encoder_reranker import CrossEncoderReranker
    from tmis.ai.schemas.citation import RetrievedChunk

    reranker = CrossEncoderReranker("cross-encoder/ms-marco-MiniLM-L-6-v2")
    chunks = [
        RetrievedChunk(
            chunk_id="unrelated",
            document_id="d1",
            content="The recipe for apple pie needs four apples.",
            score=0.9,
            metadata={},
        ),
        RetrievedChunk(
            chunk_id="relevant",
            document_id="d2",
            content="The landlord must deliver a decent home to the tenant.",
            score=0.1,
            metadata={},
        ),
    ]

    result = reranker.rerank("What are a landlord's obligations?", chunks)

    assert result[0].chunk_id == "relevant"
