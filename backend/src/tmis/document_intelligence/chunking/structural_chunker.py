from tmis.ai.rag.ports import Chunk
from tmis.document_intelligence.schemas.layout import BlockType, LayoutBlock

_DEFAULT_MAX_CHUNK_CHARS = 800
_SKIPPED_BLOCK_TYPES = frozenset({BlockType.HEADER, BlockType.FOOTER})
_SECTION_BLOCK_TYPES = frozenset({BlockType.TITLE, BlockType.SUBTITLE})


class StructuralChunker:
    """Implements `DocumentChunkerPort` by respecting the document's own
    structure: a new chunk starts at every title/subtitle, and each chunk
    carries the section title it belongs to as metadata, so context is
    never lost purely to a character-count cutoff (contrast with
    `tmis.ai.rag.chunking.FixedSizeChunker`, see
    docs/14-document-intelligence.md).
    """

    def __init__(self, max_chunk_chars: int = _DEFAULT_MAX_CHUNK_CHARS) -> None:
        self._max_chunk_chars = max_chunk_chars

    def chunk(
        self, document_id: str, text: str, layout_blocks: list[LayoutBlock]
    ) -> list[Chunk]:
        chunks: list[Chunk] = []
        buffer: list[str] = []
        current_section = "Introduction"
        chunk_index = 0

        def flush() -> None:
            nonlocal buffer, chunk_index
            if not buffer:
                return
            chunks.append(
                Chunk(
                    id=f"{document_id}::{chunk_index}",
                    document_id=document_id,
                    content="\n".join(buffer),
                    metadata={"section": current_section},
                )
            )
            chunk_index += 1
            buffer = []

        for block in layout_blocks:
            if block.type in _SKIPPED_BLOCK_TYPES:
                continue
            if block.type in _SECTION_BLOCK_TYPES:
                flush()
                current_section = block.content
                buffer.append(block.content)
                continue
            if len(block.content) >= self._max_chunk_chars:
                # A single block larger than the limit (e.g. one huge
                # unbroken paragraph) still needs to be split somewhere:
                # section boundaries always win first, size only decides
                # within an already-oversized block.
                flush()
                for start in range(0, len(block.content), self._max_chunk_chars):
                    buffer.append(block.content[start : start + self._max_chunk_chars])
                    flush()
                continue
            buffer.append(block.content)
            if sum(len(piece) for piece in buffer) >= self._max_chunk_chars:
                flush()
        flush()
        return chunks
