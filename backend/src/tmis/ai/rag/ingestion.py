from tmis.ai.rag.ports import RawDocument


class PlainTextIngestor:
    """Implements `IngestorPort` for already-extracted plain text.

    OCR/PDF extraction is handled upstream by `tmis.domain.ocr` (see
    docs/04-domain-driven-design.md); the RAG pipeline starts from text.
    """

    def ingest(
        self, raw_id: str, content: str, metadata: dict[str, str] | None = None
    ) -> RawDocument:
        return RawDocument(id=raw_id, content=content, metadata=metadata or {})
