from tmis.ai.embeddings.ports import EmbeddingProviderPort
from tmis.ai.rag.ports import Chunk
from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.case_intelligence.search.schemas import CaseSearchResult, SearchResultKind
from tmis.document_intelligence.embeddings.bridge import DocumentEmbeddingBridge


class CaseSearchEngine:
    """Implements `CaseSearchPort` on top of the Sprint 2/3 embeddings and
    RAG index (`tmis.document_intelligence.embeddings.bridge.DocumentEmbeddingBridge`),
    so case search shares its retrieval machinery with document search
    rather than reinventing it (see docs/19-case-intelligence.md).

    `reindex()` rebuilds the index from scratch every time: a case's
    aggregate content (actors, facts, events, documents) is small enough
    that a full rebuild is simpler and avoids accumulating duplicate
    entries in the underlying in-memory vector index across repeated
    updates.
    """

    def __init__(self, embedding_provider: EmbeddingProviderPort | None = None) -> None:
        self._embedding_provider = embedding_provider
        self._bridge = DocumentEmbeddingBridge(embedding_provider=embedding_provider)

    async def reindex(self, profile: CaseProfile) -> None:
        self._bridge = DocumentEmbeddingBridge(embedding_provider=self._embedding_provider)
        chunks: list[Chunk] = []

        for actor in profile.actors:
            chunks.append(
                Chunk(
                    id=f"actor::{actor.id}",
                    document_id=profile.case_id,
                    content=actor.name,
                    metadata={"kind": SearchResultKind.ACTOR.value, "ref_id": actor.id},
                )
            )
        for fact in profile.facts:
            chunks.append(
                Chunk(
                    id=f"fact::{fact.id}",
                    document_id=profile.case_id,
                    content=fact.description,
                    metadata={"kind": SearchResultKind.FACT.value, "ref_id": fact.id},
                )
            )
        for index, entry in enumerate(profile.timeline):
            chunks.append(
                Chunk(
                    id=f"event::{profile.case_id}::{index}",
                    document_id=profile.case_id,
                    content=entry.description,
                    metadata={"kind": SearchResultKind.EVENT.value, "ref_id": str(index)},
                )
            )
        for document_id in profile.document_ids:
            chunks.append(
                Chunk(
                    id=f"document::{document_id}",
                    document_id=profile.case_id,
                    content=document_id,
                    metadata={"kind": SearchResultKind.DOCUMENT.value, "ref_id": document_id},
                )
            )

        if chunks:
            await self._bridge.embed_and_index(chunks)

    async def search(self, query: str, *, top_k: int = 10) -> list[CaseSearchResult]:
        results = await self._bridge.search(query, top_k=top_k)
        return [
            CaseSearchResult(
                kind=SearchResultKind(
                    result.metadata.get("kind", SearchResultKind.REFERENCE.value)
                ),
                id=result.metadata.get("ref_id", result.chunk_id),
                label=result.content,
                score=result.score,
            )
            for result in results
        ]
