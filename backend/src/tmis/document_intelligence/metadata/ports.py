from typing import Protocol

from tmis.document_intelligence.schemas.document import IngestedDocument
from tmis.document_intelligence.schemas.metadata import DocumentMetadata
from tmis.document_intelligence.schemas.ocr import OcrResult


class MetadataExtractorPort(Protocol):
    def extract(
        self,
        document: IngestedDocument,
        ocr_result: OcrResult,
        *,
        language: str | None,
        source: str,
        version: int = 1,
    ) -> DocumentMetadata: ...
