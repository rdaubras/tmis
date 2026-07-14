from collections.abc import Sequence

from tmis.ai.embeddings.hashing_provider import HashingEmbeddingProvider
from tmis.ai.embeddings.ports import EmbeddingProviderPort
from tmis.ai.embeddings.similarity import cosine_similarity
from tmis.knowledge_graph.semantic_intelligence.ports import SemanticLinkStorePort
from tmis.knowledge_graph.semantic_intelligence.schemas import SemanticLink, new_semantic_link_id


class SemanticLinkEngine:
    """Computes `SemanticLink`s from `tmis.ai.embeddings`/`tmis.ai.rag`
    — the existing embedding infrastructure — rather than standing up
    a second embedding provider or vector index. Only pairs scoring at
    or above `similarity_threshold` are persisted, since a semantic
    link is meant to be a meaningful recommendation, not every pair's
    raw score.
    """

    def __init__(
        self,
        store: SemanticLinkStorePort,
        embedding_provider: EmbeddingProviderPort | None = None,
        similarity_threshold: float = 0.7,
    ) -> None:
        self._store = store
        self._embedding_provider = embedding_provider or HashingEmbeddingProvider()
        self._similarity_threshold = similarity_threshold

    async def link_objects(
        self, objects: Sequence[tuple[str, str]]
    ) -> list[SemanticLink]:
        """`objects` is a sequence of (id, text) pairs drawn from any
        of the three existing graphs (a `CaseNode.label`, a
        `KnowledgeNode.label`, a cabinet `KnowledgeObject.title`...).
        Every pair scoring at or above the threshold becomes one
        persisted `SemanticLink`."""
        if len(objects) < 2:
            return []

        ids = [object_id for object_id, _ in objects]
        vectors = await self._embedding_provider.embed([text for _, text in objects])

        links: list[SemanticLink] = []
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                score = cosine_similarity(vectors[i], vectors[j])
                if score < self._similarity_threshold:
                    continue
                link = SemanticLink(
                    id=new_semantic_link_id(),
                    source_id=ids[i],
                    target_id=ids[j],
                    score=score,
                    embedding_name=self._embedding_provider.embedding_name,
                )
                self._store.save(link)
                links.append(link)
        return links

    def links_for(self, object_id: str) -> list[SemanticLink]:
        return self._store.list_for_object(object_id)
