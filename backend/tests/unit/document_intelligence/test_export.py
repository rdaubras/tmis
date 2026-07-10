import json

from tmis.document_intelligence.export.json_exporter import JsonExporter
from tmis.document_intelligence.schemas.classification import (
    ClassificationResult,
    DocumentCategory,
)
from tmis.document_intelligence.schemas.document import ProcessingStatus
from tmis.document_intelligence.schemas.record import DocumentRecord


def test_export_excludes_raw_bytes_but_keeps_their_length() -> None:
    record = DocumentRecord(
        document_id="doc-1",
        filename="bail.txt",
        status=ProcessingStatus.PROCESSED,
        raw_bytes=b"hello world",
    )

    exported = json.loads(JsonExporter().export(record))

    assert exported["raw_bytes"] == "<11 bytes>"


def test_export_serializes_enums_as_their_value() -> None:
    record = DocumentRecord(
        document_id="doc-1",
        filename="bail.txt",
        status=ProcessingStatus.PROCESSED,
        raw_bytes=b"x",
        classification=ClassificationResult(category=DocumentCategory.CONTRACT, confidence=0.5),
    )

    exported = json.loads(JsonExporter().export(record))

    assert exported["status"] == "processed"
    assert exported["classification"]["category"] == "contract"


def test_export_is_valid_json_for_a_default_record() -> None:
    record = DocumentRecord(
        document_id="doc-1", filename="f.txt", status=ProcessingStatus.RECEIVED, raw_bytes=b""
    )
    exported = json.loads(JsonExporter().export(record))
    assert exported["document_id"] == "doc-1"
    assert exported["entities"] == []
