import hashlib
import math
import re

_TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class HashingEmbeddingProvider:
    """Implements `EmbeddingProviderPort` with a dependency-free, fully
    deterministic bag-of-words hashing embedding.

    This is a genuine (if crude) embedding — cosine similarity between two
    hashed vectors correlates with shared vocabulary — which is enough to
    exercise retrieval and reranking end-to-end without calling any
    external embedding API (see docs/09-roadmap-30-sprints.md, Sprint 7,
    for the real embedding model wiring).
    """

    embedding_name = "hashing-bow"

    def __init__(self, dimensions: int = 64) -> None:
        self.dimensions = dimensions

    def _hash_index(self, token: str) -> int:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        return int.from_bytes(digest[:4], "big") % self.dimensions

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in _tokenize(text):
            vector[self._hash_index(token)] += 1.0
        norm = math.sqrt(sum(v * v for v in vector))
        if norm == 0:
            return vector
        return [v / norm for v in vector]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]
