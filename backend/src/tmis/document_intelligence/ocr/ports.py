from typing import Protocol

from tmis.document_intelligence.schemas.document import IngestedDocument
from tmis.document_intelligence.schemas.ocr import OcrResult


class OcrEnginePort(Protocol):
    """Port implemented by every interchangeable OCR engine.

    Takes the `IngestedDocument` (not raw bytes) so a passthrough engine
    can reuse text a parser already extracted (PDF/DOCX/TXT), while an
    image-OCR engine can be plugged in later to fill `text` for documents
    the parser left empty (scanned images) — see
    docs/16-guide-nouveau-moteur-ocr.md.
    """

    engine_name: str

    def extract_text(self, document: IngestedDocument) -> OcrResult: ...


class LanguageDetectorPort(Protocol):
    def detect(self, text: str) -> str | None: ...


class RotationDetectorPort(Protocol):
    """Detects the rotation (in degrees) that should be applied to a
    scanned page before OCR. Sprint 3 ships a stub — see
    docs/14-document-intelligence.md."""

    def detect_rotation(self, raw_bytes: bytes) -> int: ...
