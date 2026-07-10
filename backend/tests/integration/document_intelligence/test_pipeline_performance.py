import time

import pytest

from tmis.document_intelligence.pipeline.document_pipeline import DocumentIntelligencePipeline

# Generous ceiling for a fully in-memory, network-free pipeline run — this
# is a regression guard against an accidental O(n^2)/pathological change,
# not a production SLA (see docs/14-document-intelligence.md).
_MAX_DURATION_SECONDS = 5.0


@pytest.mark.asyncio
async def test_processing_a_typical_document_completes_quickly() -> None:
    text = (
        "CONTRAT DE BAIL COMMERCIAL\n\n"
        + "Le présent contrat est conclu entre les parties. " * 50
        + "\n\n1.1 Modalités de paiement\n\n"
        + "Le loyer mensuel est de 1500 EUR, payable le 5 de chaque mois. " * 50
    )
    pipeline = DocumentIntelligencePipeline()

    start = time.perf_counter()
    record = await pipeline.process("bail.txt", "text/plain", text.encode())
    duration = time.perf_counter() - start

    assert duration < _MAX_DURATION_SECONDS
    assert record.status.value == "processed"


@pytest.mark.asyncio
async def test_processing_scales_reasonably_with_document_count() -> None:
    pipeline = DocumentIntelligencePipeline()
    text = "Un contrat quelconque signé le 12 janvier 2019. " * 20

    start = time.perf_counter()
    for i in range(20):
        await pipeline.process(f"doc-{i}.txt", "text/plain", text.encode())
    duration = time.perf_counter() - start

    assert duration < _MAX_DURATION_SECONDS
    assert len(pipeline.document_store.list_ids()) == 20


@pytest.mark.asyncio
async def test_every_stage_reports_a_non_negative_duration() -> None:
    pipeline = DocumentIntelligencePipeline()
    record = await pipeline.process("bail.txt", "text/plain", b"Un texte quelconque.")

    metrics = pipeline.evaluator.for_document(record.document_id)[0]

    assert all(stage.duration_ms >= 0 for stage in metrics.stage_metrics)
    assert metrics.total_duration_ms >= sum(s.duration_ms for s in metrics.stage_metrics) * 0.9
