from typing import Protocol


class EmbeddingProviderPort(Protocol):
    """Port implemented by every interchangeable embedding model adapter."""

    embedding_name: str
    dimensions: int

    async def embed(self, texts: list[str]) -> list[list[float]]: ...
