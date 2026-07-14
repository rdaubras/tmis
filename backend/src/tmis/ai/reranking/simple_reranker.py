from tmis.ai.schemas.citation import RetrievedChunk


class KeywordOverlapReranker:
    """Implements `RerankerPort` with a small, explainable boost: chunks
    that contain the query as an exact phrase are promoted above chunks
    that only matched on individual tokens or vector similarity.

    A learned cross-encoder reranker was added at Sprint 28 (see
    `tmis.ai.reranking.adapters.cross_encoder_reranker.CrossEncoderReranker`
    and docs/09-roadmap-30-sprints.md); this deterministic rule remains the
    default in dev/tests and the fallback whenever the cross-encoder model
    is unavailable.
    """

    def __init__(self, exact_phrase_bonus: float = 0.2) -> None:
        self._exact_phrase_bonus = exact_phrase_bonus

    def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        needle = query.lower().strip()
        boosted = [
            RetrievedChunk(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                content=chunk.content,
                score=chunk.score + self._exact_phrase_bonus
                if needle and needle in chunk.content.lower()
                else chunk.score,
                metadata=chunk.metadata,
            )
            for chunk in chunks
        ]
        boosted.sort(key=lambda c: c.score, reverse=True)
        return boosted
