from tmis.document_intelligence.schemas.document import IngestedDocument
from tmis.document_intelligence.schemas.ocr import OcrResult


class NullOcrEngine:
    """Implements `OcrEnginePort` as a placeholder for scanned images.

    Sprint 3 scope: no real image-to-text engine is wired yet (see
    docs/16-guide-nouveau-moteur-ocr.md) — this returns an explicitly
    low-confidence empty result rather than silently pretending the image
    was read.
    """

    engine_name = "null"

    def extract_text(self, document: IngestedDocument) -> OcrResult:
        return OcrResult(text="", confidence=0.0, engine=self.engine_name)
