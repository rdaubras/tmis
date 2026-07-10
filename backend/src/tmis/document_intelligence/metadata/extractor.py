import hashlib

from tmis.document_intelligence.schemas.document import IngestedDocument
from tmis.document_intelligence.schemas.metadata import DocumentMetadata
from tmis.document_intelligence.schemas.ocr import OcrResult


class DefaultMetadataExtractor:
    """Implements `MetadataExtractorPort` from the fields already gathered
    by ingestion and OCR — no extra external lookups needed."""

    def extract(
        self,
        document: IngestedDocument,
        ocr_result: OcrResult,
        *,
        language: str | None,
        source: str,
        version: int = 1,
    ) -> DocumentMetadata:
        return DocumentMetadata(
            author=document.metadata.get("author"),
            created_at=document.metadata.get("created_at"),
            language=language,
            content_type=document.content_type,
            size_bytes=len(document.raw_bytes),
            page_count=document.page_count,
            source=source,
            version=version,
            sha256=hashlib.sha256(document.raw_bytes).hexdigest(),
            ocr_confidence=ocr_result.confidence,
        )
