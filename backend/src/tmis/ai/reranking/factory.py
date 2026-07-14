from tmis.ai.reranking.ports import RerankerPort
from tmis.ai.reranking.simple_reranker import KeywordOverlapReranker
from tmis.core.config import get_settings
from tmis.core.logging import get_logger

logger = get_logger(__name__)


def get_reranker() -> RerankerPort:
    """Single composition point deciding `KeywordOverlapReranker` vs
    `CrossEncoderReranker` (see docs/156-guide-reranker.md), mirroring
    `tmis.ai.embeddings.factory.get_embedding_provider`.

    Defaults to `KeywordOverlapReranker` — dev/tests keep working with zero
    external dependency and no model download unless
    `TMIS_RERANKER_BACKEND=cross_encoder` is set explicitly. Even then, any
    failure to load the model (package not installed, no network for the
    first download, corrupt cache...) falls back to `KeywordOverlapReranker`
    rather than crashing startup.
    """
    settings = get_settings()
    if settings.reranker_backend != "cross_encoder":
        return KeywordOverlapReranker()

    from tmis.ai.reranking.adapters.cross_encoder_reranker import CrossEncoderReranker

    try:
        reranker = CrossEncoderReranker(settings.cross_encoder_model_name)
    except Exception as exc:  # noqa: BLE001 — a broken/offline model load must never crash startup
        logger.warning(
            "reranker.cross_encoder_unavailable",
            model=settings.cross_encoder_model_name,
            error=str(exc),
        )
        return KeywordOverlapReranker()

    logger.info(
        "reranker.backend_selected",
        backend="cross_encoder",
        model=settings.cross_encoder_model_name,
    )
    return reranker
