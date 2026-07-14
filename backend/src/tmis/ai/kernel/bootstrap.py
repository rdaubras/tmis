from functools import lru_cache

from tmis.ai.connectors.factory import (
    build_codes_connector,
    build_doctrine_connector,
    build_jurisprudence_connector,
)
from tmis.ai.connectors.manager import ConnectorManager
from tmis.ai.embeddings.factory import get_embedding_provider
from tmis.ai.kernel.kernel import TMISKernel
from tmis.ai.rag.factory import get_vector_index
from tmis.ai.rag.pipeline import RagPipeline
from tmis.ai.reranking.factory import get_reranker


@lru_cache
def get_kernel() -> TMISKernel:
    """Process-wide `TMISKernel` singleton.

    Shared by the API layer and every engine built on top of it (Document
    Intelligence, Case Intelligence) so they all publish/subscribe on the
    same `EventBus` — the seam that makes the "living case" automatic
    (see docs/10-ai-kernel.md and docs/19-case-intelligence.md).

    Sprint 27: the embedding provider, vector index, and codes/
    jurisprudence/doctrine connectors are picked here from central config
    (`tmis.ai.embeddings.factory`, `tmis.ai.rag.factory`,
    `tmis.ai.connectors.factory`) — real adapters if configured, the
    Sprint 2 in-memory/fixture defaults otherwise. Sprint 28 adds the
    reranker (`tmis.ai.reranking.factory.get_reranker`) on the same
    principle. `TMISKernel` itself is unchanged: this is the single place
    that decides, everything else keeps depending on the ports.
    """
    embedding_provider = get_embedding_provider()
    connector_manager = ConnectorManager(
        codes=build_codes_connector(),
        jurisprudence=build_jurisprudence_connector(),
        doctrine=build_doctrine_connector(),
    )
    return TMISKernel(
        connector_manager=connector_manager,
        embedding_provider=embedding_provider,
        rag=RagPipeline(
            embedding_provider=embedding_provider,
            index=get_vector_index(dimensions=embedding_provider.dimensions),
            reranker=get_reranker(),
        ),
    )
