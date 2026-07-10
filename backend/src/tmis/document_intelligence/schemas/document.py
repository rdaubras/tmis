from dataclasses import dataclass, field
from enum import Enum


class ProcessingStatus(str, Enum):
    RECEIVED = "received"
    VALIDATED = "validated"
    SCANNED = "scanned"
    OCR_DONE = "ocr_done"
    STRUCTURED = "structured"
    CLASSIFIED = "classified"
    METADATA_EXTRACTED = "metadata_extracted"
    ENTITIES_EXTRACTED = "entities_extracted"
    TIMELINE_BUILT = "timeline_built"
    CHUNKED = "chunked"
    EMBEDDED = "embedded"
    KNOWLEDGE_UPDATED = "knowledge_updated"
    STORED = "stored"
    PROCESSED = "processed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class IngestedDocument:
    """The result of parsing a raw file into extractable text, before any
    OCR/structure/classification analysis happens.

    `raw_bytes` is kept alongside `text` (empty for scanned images) so a
    future real OCR engine has the original bytes to work with — see
    `tmis.document_intelligence.ocr.ports.OcrEnginePort`.
    """

    id: str
    filename: str
    content_type: str
    text: str
    page_count: int
    raw_bytes: bytes = b""
    metadata: dict[str, str] = field(default_factory=dict)
