from tmis.document_intelligence.ocr.engines.null_engine import NullOcrEngine
from tmis.document_intelligence.ocr.engines.passthrough_engine import PassthroughOcrEngine
from tmis.document_intelligence.ocr.ports import OcrEnginePort
from tmis.document_intelligence.schemas.document import IngestedDocument
from tmis.document_intelligence.schemas.ocr import OcrResult


class OcrEngineRegistry:
    """Selects the OCR engine to run for a given `IngestedDocument`.

    Sprint 3 scope: documents that already carry extractable text use the
    passthrough engine; documents with no text (scanned images) fall back
    to the null engine. See docs/16-guide-nouveau-moteur-ocr.md for how a
    real image-OCR engine takes over the second branch.
    """

    def __init__(
        self,
        *,
        text_engine: OcrEnginePort | None = None,
        image_engine: OcrEnginePort | None = None,
    ) -> None:
        self._text_engine: OcrEnginePort = text_engine or PassthroughOcrEngine()
        self._image_engine: OcrEnginePort = image_engine or NullOcrEngine()

    def select(self, document: IngestedDocument) -> OcrEnginePort:
        return self._text_engine if document.text else self._image_engine

    def extract_text(self, document: IngestedDocument) -> OcrResult:
        return self.select(document).extract_text(document)
