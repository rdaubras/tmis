from tmis.ai.schemas.citation import RetrievedChunk


class CrossEncoderReranker:
    """Implements `RerankerPort` with a real learned cross-encoder model
    from sentence-transformers (deferred import — see `tmis.ai.embeddings.
    adapters.sentence_transformer_provider.SentenceTransformerEmbeddingProvider`
    for the same pattern), scoring each `(query, chunk)` pair jointly
    instead of `KeywordOverlapReranker`'s keyword-overlap heuristic (see
    docs/156-guide-reranker.md).
    """

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import CrossEncoder  # deferred: heavy, optional import

        self.model_name = model_name
        self._model = CrossEncoder(model_name)

    def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        if not chunks:
            return []

        pairs = [(query, chunk.content) for chunk in chunks]
        scores = self._model.predict(pairs)

        rescored = [
            RetrievedChunk(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                content=chunk.content,
                score=float(score),
                metadata=chunk.metadata,
            )
            for chunk, score in zip(chunks, scores, strict=True)
        ]
        rescored.sort(key=lambda c: c.score, reverse=True)
        return rescored
