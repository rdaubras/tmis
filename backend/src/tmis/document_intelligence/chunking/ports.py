from typing import Protocol

from tmis.ai.rag.ports import Chunk
from tmis.document_intelligence.schemas.layout import LayoutBlock


class DocumentChunkerPort(Protocol):
    """Port implemented by every interchangeable chunking strategy.

    Returns `tmis.ai.rag.ports.Chunk` so chunks flow directly into the
    embeddings bridge (`tmis.document_intelligence.embeddings`), itself
    built on the Sprint 2 RAG module.
    """

    def chunk(
        self, document_id: str, text: str, layout_blocks: list[LayoutBlock]
    ) -> list[Chunk]: ...
