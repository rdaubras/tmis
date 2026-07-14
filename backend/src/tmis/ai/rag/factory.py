from tmis.ai.rag.adapters.qdrant_client_factory import get_qdrant_client
from tmis.ai.rag.adapters.qdrant_index import QdrantVectorIndex
from tmis.ai.rag.indexing import InMemoryVectorIndex
from tmis.ai.rag.ports import IndexPort
from tmis.core.config import get_settings
from tmis.core.logging import get_logger

logger = get_logger(__name__)


def get_vector_index(*, dimensions: int) -> IndexPort:
    """Single composition point deciding `InMemoryVectorIndex` vs
    `QdrantVectorIndex`, so every caller (the AI Kernel, the RAG pipeline)
    gets the same answer for the same config instead of each guessing
    independently (see docs/153-architecture-rag-production.md).

    Defaults to `InMemoryVectorIndex` — dev/tests keep working with zero
    external dependency unless `TMIS_RAG_VECTOR_INDEX_BACKEND=qdrant` is
    set explicitly.
    """
    settings = get_settings()
    if settings.rag_vector_index_backend != "qdrant":
        return InMemoryVectorIndex()

    logger.info(
        "rag_vector_index.backend_selected",
        backend="qdrant",
        collection=settings.qdrant_collection,
        url=settings.qdrant_url,
    )
    return QdrantVectorIndex(
        get_qdrant_client(),
        collection_name=settings.qdrant_collection,
        dimensions=dimensions,
    )
