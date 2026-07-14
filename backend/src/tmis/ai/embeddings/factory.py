from tmis.ai.embeddings.adapters.sentence_transformer_provider import (
    SentenceTransformerEmbeddingProvider,
)
from tmis.ai.embeddings.hashing_provider import HashingEmbeddingProvider
from tmis.ai.embeddings.ports import EmbeddingProviderPort
from tmis.core.config import get_settings
from tmis.core.logging import get_logger

logger = get_logger(__name__)


def get_embedding_provider() -> EmbeddingProviderPort:
    """Single composition point deciding `HashingEmbeddingProvider` vs
    `SentenceTransformerEmbeddingProvider` (see
    docs/153-architecture-rag-production.md).

    Defaults to `HashingEmbeddingProvider` — dev/tests keep working with
    zero external dependency and no model download unless
    `TMIS_EMBEDDING_BACKEND=sentence_transformers` is set explicitly. Even
    then, any failure to load the model (package not installed, no network
    for the first download, corrupt cache...) falls back to
    `HashingEmbeddingProvider` rather than crashing startup.
    """
    settings = get_settings()
    if settings.embedding_backend != "sentence_transformers":
        return HashingEmbeddingProvider()

    try:
        provider = SentenceTransformerEmbeddingProvider(settings.sentence_transformer_model_name)
    except Exception as exc:  # noqa: BLE001 — a broken/offline model load must never crash startup
        logger.warning(
            "embedding_provider.sentence_transformers_unavailable",
            model=settings.sentence_transformer_model_name,
            error=str(exc),
        )
        return HashingEmbeddingProvider()

    logger.info(
        "embedding_provider.backend_selected",
        backend="sentence_transformers",
        model=settings.sentence_transformer_model_name,
        dimensions=provider.dimensions,
    )
    return provider
