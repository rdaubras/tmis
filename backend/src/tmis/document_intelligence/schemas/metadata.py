from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DocumentMetadata:
    author: str | None
    created_at: str | None
    language: str | None
    content_type: str
    size_bytes: int
    page_count: int
    source: str
    version: int
    sha256: str
    ocr_confidence: float | None
