import io

from pypdf import PdfReader

from tmis.document_intelligence.schemas.document import IngestedDocument

_PAGE_BREAK = "\x0c"


class PdfParser:
    """Implements `DocumentParserPort` for PDF files using `pypdf`.

    Pages are joined with a form-feed character (`\\x0c`) so downstream
    layout analysis can detect page boundaries (headers/footers) without
    needing the original PDF structure.
    """

    content_types: tuple[str, ...] = ("application/pdf",)

    def supports(self, content_type: str) -> bool:
        return content_type in self.content_types

    def parse(self, document_id: str, filename: str, raw_bytes: bytes) -> IngestedDocument:
        reader = PdfReader(io.BytesIO(raw_bytes))
        pages_text = [page.extract_text() or "" for page in reader.pages]
        metadata = {}
        if reader.metadata:
            if reader.metadata.author:
                metadata["author"] = reader.metadata.author
            if reader.metadata.creation_date:
                metadata["created_at"] = reader.metadata.creation_date.isoformat()

        return IngestedDocument(
            id=document_id,
            filename=filename,
            content_type="application/pdf",
            text=_PAGE_BREAK.join(pages_text),
            page_count=len(reader.pages),
            raw_bytes=raw_bytes,
            metadata=metadata,
        )
