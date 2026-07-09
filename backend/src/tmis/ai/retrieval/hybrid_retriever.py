import re

from tmis.ai.embeddings.ports import EmbeddingProviderPort
from tmis.ai.rag.ports import IndexPort
from tmis.ai.schemas.citation import RetrievedChunk

_TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _lexical_overlap(query_tokens: set[str], content: str) -> float:
    if not query_tokens:
        return 0.0
    content_tokens = _tokens(content)
    if not content_tokens:
        return 0.0
    return len(query_tokens & content_tokens) / len(query_tokens)


class HybridRetriever:
    """Implements `RetrieverPort` by combining vector similarity (from the
    RAG index) with lexical keyword overlap, so both open questions and
    precise references (an article number, a case reference) are covered
    (see docs/06-strategie-rag.md).
    """

    def __init__(
        self,
        index: IndexPort,
        embedding_provider: EmbeddingProviderPort,
        *,
        vector_weight: float = 0.5,
        candidate_pool_multiplier: int = 3,
    ) -> None:
        self._index = index
        self._embedding_provider = embedding_provider
        self._vector_weight = vector_weight
        self._candidate_pool_multiplier = candidate_pool_multiplier

    async def retrieve(
        self, query: str, *, top_k: int = 5, filters: dict[str, str] | None = None
    ) -> list[RetrievedChunk]:
        [query_vector] = await self._embedding_provider.embed([query])
        candidates = await self._index.search(
            query_vector, top_k=top_k * self._candidate_pool_multiplier, filters=filters
        )

        query_tokens = _tokens(query)
        hybrid: list[RetrievedChunk] = []
        for candidate in candidates:
            lexical_score = _lexical_overlap(query_tokens, candidate.content)
            combined = (
                self._vector_weight * candidate.score
                + (1 - self._vector_weight) * lexical_score
            )
            hybrid.append(
                RetrievedChunk(
                    chunk_id=candidate.chunk_id,
                    document_id=candidate.document_id,
                    content=candidate.content,
                    score=combined,
                    metadata=candidate.metadata,
                )
            )
        hybrid.sort(key=lambda c: c.score, reverse=True)
        return hybrid[:top_k]
