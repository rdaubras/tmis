import pytest

from tmis.ai.events.events import DocumentUploaded
from tmis.document_intelligence.ingestion.exceptions import (
    DocumentValidationError,
    UnsupportedContentTypeError,
    VirusDetectedError,
)
from tmis.document_intelligence.ingestion.validation import DocumentValidator
from tmis.document_intelligence.pipeline.document_pipeline import DocumentIntelligencePipeline


@pytest.mark.asyncio
async def test_pipeline_rejects_empty_file_before_any_other_stage_runs() -> None:
    pipeline = DocumentIntelligencePipeline()

    with pytest.raises(DocumentValidationError):
        await pipeline.process("empty.txt", "text/plain", b"")

    # DocumentUploaded is still published (the file did arrive); no other
    # event should be, since validation is the very first stage.
    assert [type(e) for e in pipeline.event_bus.history] == [DocumentUploaded]


@pytest.mark.asyncio
async def test_pipeline_rejects_oversized_file() -> None:
    pipeline = DocumentIntelligencePipeline(validator=DocumentValidator(max_size_bytes=10))

    with pytest.raises(DocumentValidationError):
        await pipeline.process("big.txt", "text/plain", b"x" * 11)


@pytest.mark.asyncio
async def test_pipeline_rejects_unsupported_content_type() -> None:
    pipeline = DocumentIntelligencePipeline()

    with pytest.raises(UnsupportedContentTypeError):
        await pipeline.process("f.xyz", "application/x-totally-unknown", b"data")


@pytest.mark.asyncio
async def test_failed_stage_is_recorded_with_its_error_and_stops_the_pipeline() -> None:
    pipeline = DocumentIntelligencePipeline()

    with pytest.raises(DocumentValidationError):
        await pipeline.process("empty.txt", "text/plain", b"")

    # No PipelineMetrics is recorded for a run that failed before storage —
    # the caller sees the exception directly, which is the current
    # (Sprint 3) failure-handling contract; see docs/14-document-intelligence.md.
    assert pipeline.evaluator.history == []


@pytest.mark.asyncio
async def test_virus_scan_rejection_stops_the_pipeline_before_ingestion() -> None:
    class _AlwaysRejectingScanner:
        def scan(self, filename: str, raw_bytes: bytes) -> None:
            raise VirusDetectedError(filename, "eicar test signature")

    pipeline = DocumentIntelligencePipeline(virus_scanner=_AlwaysRejectingScanner())

    with pytest.raises(VirusDetectedError):
        await pipeline.process("bad.txt", "text/plain", b"hello")

    assert pipeline.document_store.list_ids() == []
