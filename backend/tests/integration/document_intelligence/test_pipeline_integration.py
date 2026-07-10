import io

import docx
import pytest
from pdf_fixture import build_minimal_pdf

from tmis.ai.events.events import (
    DocumentProcessed,
    DocumentUploaded,
    EmbeddingsCreated,
    EntitiesExtracted,
    KnowledgeUpdated,
    LayoutDetected,
    MetadataExtracted,
    OCRCompleted,
    TimelineBuilt,
)
from tmis.document_intelligence.pipeline.document_pipeline import DocumentIntelligencePipeline
from tmis.document_intelligence.schemas.document import ProcessingStatus

_CONTRACT_TEXT = (
    "CONTRAT DE BAIL COMMERCIAL\n\n"
    "Le présent contrat a été signé le 12 janvier 2019 entre Maître Jean Dupont "
    "et la société ACME SARL, domiciliée au 12 rue de la Paix, 75002 Paris.\n\n"
    "1.1 Modalités de paiement\n\n"
    "Le loyer mensuel est de 1500 EUR, payable le 5 de chaque mois. "
    "Voir article 1240 du code civil.\n\n"
    "Fait à Paris, le 12 janvier 2019."
)


def _docx_bytes(text: str) -> bytes:
    document = docx.Document()
    for line in text.split("\n\n"):
        document.add_paragraph(line)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_full_pipeline_processes_a_text_document() -> None:
    pipeline = DocumentIntelligencePipeline()

    record = await pipeline.process("bail.txt", "text/plain", _CONTRACT_TEXT.encode())

    assert record.status == ProcessingStatus.PROCESSED
    assert record.classification is not None
    assert record.metadata is not None
    assert record.metadata.sha256
    assert len(record.entities) > 0
    assert len(record.timeline_events) >= 1
    assert len(record.chunk_ids) > 0
    assert record.warnings == []


@pytest.mark.asyncio
async def test_full_pipeline_processes_a_pdf_document() -> None:
    pipeline = DocumentIntelligencePipeline()
    pdf_bytes = build_minimal_pdf("Hello World")

    record = await pipeline.process("doc.pdf", "application/pdf", pdf_bytes)

    assert record.status == ProcessingStatus.PROCESSED
    assert "Hello World" in record.ocr_text


@pytest.mark.asyncio
async def test_full_pipeline_processes_a_docx_document() -> None:
    pipeline = DocumentIntelligencePipeline()
    docx_bytes = _docx_bytes(_CONTRACT_TEXT)

    docx_content_type = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    record = await pipeline.process("bail.docx", docx_content_type, docx_bytes)

    assert record.status == ProcessingStatus.PROCESSED
    assert len(record.entities) > 0


@pytest.mark.asyncio
async def test_pipeline_publishes_all_nine_document_events_in_order() -> None:
    pipeline = DocumentIntelligencePipeline()
    await pipeline.process("bail.txt", "text/plain", _CONTRACT_TEXT.encode())

    event_types = [type(event) for event in pipeline.event_bus.history]

    assert event_types == [
        DocumentUploaded,
        OCRCompleted,
        LayoutDetected,
        MetadataExtracted,
        EntitiesExtracted,
        TimelineBuilt,
        EmbeddingsCreated,
        KnowledgeUpdated,
        DocumentProcessed,
    ]


@pytest.mark.asyncio
async def test_pipeline_persists_the_record_in_the_document_store() -> None:
    pipeline = DocumentIntelligencePipeline()
    record = await pipeline.process("bail.txt", "text/plain", _CONTRACT_TEXT.encode())

    stored = pipeline.document_store.get(record.document_id)

    assert stored == record


@pytest.mark.asyncio
async def test_pipeline_updates_the_knowledge_graph() -> None:
    pipeline = DocumentIntelligencePipeline()
    record = await pipeline.process("bail.txt", "text/plain", _CONTRACT_TEXT.encode())

    document_node = pipeline.knowledge_graph.get_node(record.document_id)

    assert document_node is not None
    assert document_node.label == "bail.txt"
    assert len(pipeline.knowledge_graph.get_neighbors(record.document_id)) > 0


@pytest.mark.asyncio
async def test_pipeline_indexes_chunks_for_semantic_search() -> None:
    pipeline = DocumentIntelligencePipeline()
    await pipeline.process("bail.txt", "text/plain", _CONTRACT_TEXT.encode())

    results = await pipeline.embedding_bridge.search("bail commercial")

    assert len(results) > 0


@pytest.mark.asyncio
async def test_pipeline_records_evaluation_metrics_for_every_stage() -> None:
    pipeline = DocumentIntelligencePipeline()
    record = await pipeline.process("bail.txt", "text/plain", _CONTRACT_TEXT.encode())

    metrics = pipeline.evaluator.for_document(record.document_id)

    assert len(metrics) == 1
    stage_names = [s.stage for s in metrics[0].stage_metrics]
    assert stage_names == [
        "validation",
        "virus_scan",
        "ingestion",
        "ocr",
        "language_detection",
        "layout",
        "classification",
        "metadata",
        "entities",
        "timeline",
        "chunking",
        "embeddings",
        "knowledge",
        "storage",
    ]
    assert metrics[0].error_count == 0
