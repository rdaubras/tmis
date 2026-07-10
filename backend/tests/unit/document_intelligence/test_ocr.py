from tmis.document_intelligence.ocr.engines.null_engine import NullOcrEngine
from tmis.document_intelligence.ocr.engines.passthrough_engine import PassthroughOcrEngine
from tmis.document_intelligence.ocr.language_detector import HeuristicLanguageDetector
from tmis.document_intelligence.ocr.registry import OcrEngineRegistry
from tmis.document_intelligence.ocr.rotation_detector import NullRotationDetector
from tmis.document_intelligence.schemas.document import IngestedDocument


def _document(text: str) -> IngestedDocument:
    return IngestedDocument(
        id="id-1", filename="f.txt", content_type="text/plain", text=text, page_count=1
    )


class TestPassthroughOcrEngine:
    def test_returns_existing_text_with_full_confidence(self) -> None:
        result = PassthroughOcrEngine().extract_text(_document("hello"))
        assert result.text == "hello"
        assert result.confidence == 1.0
        assert result.engine == "passthrough"


class TestNullOcrEngine:
    def test_returns_empty_text_with_zero_confidence(self) -> None:
        result = NullOcrEngine().extract_text(_document(""))
        assert result.text == ""
        assert result.confidence == 0.0


class TestOcrEngineRegistry:
    def test_selects_passthrough_for_documents_with_text(self) -> None:
        registry = OcrEngineRegistry()
        result = registry.extract_text(_document("some text"))
        assert result.engine == "passthrough"

    def test_selects_null_engine_for_documents_without_text(self) -> None:
        registry = OcrEngineRegistry()
        result = registry.extract_text(_document(""))
        assert result.engine == "null"


class TestHeuristicLanguageDetector:
    def test_detects_french(self) -> None:
        detector = HeuristicLanguageDetector()
        assert detector.detect("Le contrat est conclu entre les parties pour une durée.") == "fr"

    def test_detects_english(self) -> None:
        detector = HeuristicLanguageDetector()
        assert detector.detect("This is the contract between the parties for a term.") == "en"

    def test_returns_none_for_empty_text(self) -> None:
        assert HeuristicLanguageDetector().detect("") is None

    def test_returns_none_when_no_stopwords_match(self) -> None:
        assert HeuristicLanguageDetector().detect("xyzxyz qwrtpl") is None


class TestNullRotationDetector:
    def test_always_returns_zero(self) -> None:
        assert NullRotationDetector().detect_rotation(b"any-bytes") == 0
