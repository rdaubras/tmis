from tmis.ai.rag.ports import Chunk, RawDocument


class FixedSizeChunker:
    """Implements `ChunkerPort` with a fixed-size sliding window and
    configurable overlap.

    Semantic chunking (by article/clause) is planned for Sprint 7 (see
    docs/06-strategie-rag.md); this deterministic splitter is enough to
    exercise indexing, retrieval and reranking today.
    """

    def __init__(self, chunk_size: int = 400, overlap: int = 50) -> None:
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        self._chunk_size = chunk_size
        self._overlap = overlap

    def chunk(self, document: RawDocument) -> list[Chunk]:
        content = document.content
        if not content:
            return []
        step = self._chunk_size - self._overlap
        chunks: list[Chunk] = []
        start = 0
        index = 0
        while start < len(content):
            piece = content[start : start + self._chunk_size]
            chunks.append(
                Chunk(
                    id=f"{document.id}::{index}",
                    document_id=document.id,
                    content=piece,
                    metadata=document.metadata,
                )
            )
            index += 1
            start += step
        return chunks
