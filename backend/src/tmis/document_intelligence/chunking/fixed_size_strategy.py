from tmis.ai.rag.chunking import FixedSizeChunker
from tmis.ai.rag.ports import Chunk, RawDocument
from tmis.document_intelligence.schemas.layout import LayoutBlock


class FixedSizeChunkingStrategy:
    """Adapts `tmis.ai.rag.chunking.FixedSizeChunker` to `DocumentChunkerPort`
    so it can be compared against `StructuralChunker` on the same
    document — ignores `layout_blocks` entirely, which is exactly the
    behaviour the comparison is meant to highlight (see
    docs/14-document-intelligence.md).
    """

    def __init__(self, chunk_size: int = 400, overlap: int = 50) -> None:
        self._chunker = FixedSizeChunker(chunk_size=chunk_size, overlap=overlap)

    def chunk(
        self, document_id: str, text: str, layout_blocks: list[LayoutBlock]
    ) -> list[Chunk]:
        return self._chunker.chunk(RawDocument(id=document_id, content=text))
