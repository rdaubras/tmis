from tmis.document_intelligence.schemas.document import IngestedDocument
from tmis.document_intelligence.schemas.ocr import OcrResult


class PassthroughOcrEngine:
    """Implements `OcrEnginePort` for documents that already have
    extractable text (PDF, DOCX, TXT) — no image-to-text work is needed,
    so this engine just carries the parser's text through with full
    confidence."""

    engine_name = "passthrough"

    def extract_text(self, document: IngestedDocument) -> OcrResult:
        return OcrResult(text=document.text, confidence=1.0, engine=self.engine_name)
