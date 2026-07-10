from tmis.document_intelligence.schemas.document import IngestedDocument


class TxtParser:
    """Implements `DocumentParserPort` for plain text files."""

    content_types: tuple[str, ...] = ("text/plain",)

    def supports(self, content_type: str) -> bool:
        return content_type in self.content_types

    def parse(self, document_id: str, filename: str, raw_bytes: bytes) -> IngestedDocument:
        text = raw_bytes.decode("utf-8", errors="replace")
        return IngestedDocument(
            id=document_id,
            filename=filename,
            content_type="text/plain",
            text=text,
            page_count=1,
            raw_bytes=raw_bytes,
        )
