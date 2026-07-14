import asyncio


class SentenceTransformerEmbeddingProvider:
    """Implements `EmbeddingProviderPort` with a local sentence-transformers
    model — a real, semantically meaningful embedding model that needs no
    external API key or network call at inference time (only a one-time
    model download to a local cache on first use), unlike a hosted
    embeddings API (see docs/153-architecture-rag-production.md for why
    this was chosen as the default *real* backend over an API-key-gated
    provider).
    """

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer  # deferred: heavy, optional import

        self.embedding_name = f"sentence-transformers:{model_name}"
        self._model = SentenceTransformer(model_name)

        dimensions = self._model.get_sentence_embedding_dimension()
        if dimensions is None:
            raise RuntimeError(
                f"could not determine embedding dimensions for model {model_name!r}"
            )
        self.dimensions = dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # `.encode()` is CPU-bound and synchronous; run it off the event
        # loop so it doesn't block other coroutines.
        vectors = await asyncio.to_thread(
            self._model.encode, texts, normalize_embeddings=True
        )
        return [vector.tolist() for vector in vectors]
