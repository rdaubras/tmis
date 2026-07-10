import hashlib

from tmis.document_intelligence.metadata.extractor import DefaultMetadataExtractor
from tmis.document_intelligence.schemas.document import IngestedDocument
from tmis.document_intelligence.schemas.ocr import OcrResult


def test_extracts_expected_metadata_fields() -> None:
    raw = b"Le contrat de bail."
    document = IngestedDocument(
        id="id-1",
        filename="bail.txt",
        content_type="text/plain",
        text="Le contrat de bail.",
        page_count=1,
        raw_bytes=raw,
        metadata={"author": "Jean Dupont", "created_at": "2024-01-01"},
    )
    ocr_result = OcrResult(text=document.text, confidence=0.87, engine="passthrough")

    metadata = DefaultMetadataExtractor().extract(
        document, ocr_result, language="fr", source="upload", version=2
    )

    assert metadata.author == "Jean Dupont"
    assert metadata.created_at == "2024-01-01"
    assert metadata.language == "fr"
    assert metadata.content_type == "text/plain"
    assert metadata.size_bytes == len(raw)
    assert metadata.page_count == 1
    assert metadata.source == "upload"
    assert metadata.version == 2
    assert metadata.sha256 == hashlib.sha256(raw).hexdigest()
    assert metadata.ocr_confidence == 0.87


def test_missing_author_and_created_at_are_none() -> None:
    document = IngestedDocument(
        id="id-1", filename="f.txt", content_type="text/plain", text="x", page_count=1
    )
    ocr_result = OcrResult(text="x", confidence=1.0, engine="passthrough")

    metadata = DefaultMetadataExtractor().extract(
        document, ocr_result, language=None, source="upload"
    )

    assert metadata.author is None
    assert metadata.created_at is None
    assert metadata.version == 1
