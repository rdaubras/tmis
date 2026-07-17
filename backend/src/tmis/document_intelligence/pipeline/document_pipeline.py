import time
import uuid
from collections.abc import Awaitable, Callable
from typing import TypeVar

from tmis.ai.events.bus import EventBus
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
from tmis.core.logging import get_logger
from tmis.document_intelligence.chunking.ports import DocumentChunkerPort
from tmis.document_intelligence.chunking.structural_chunker import StructuralChunker
from tmis.document_intelligence.classification.keyword_classifier import KeywordClassifier
from tmis.document_intelligence.classification.ports import ClassifierPort
from tmis.document_intelligence.embeddings.bridge import DocumentEmbeddingBridge
from tmis.document_intelligence.entities.ports import EntityExtractorPort
from tmis.document_intelligence.entities.regex_extractor import RegexEntityExtractor
from tmis.document_intelligence.evaluation.evaluator import PipelineEvaluator
from tmis.document_intelligence.evaluation.metrics import PipelineMetrics, StageMetric
from tmis.document_intelligence.ingestion.ports import VirusScanPort
from tmis.document_intelligence.ingestion.registry import IngestionRegistry
from tmis.document_intelligence.ingestion.validation import DocumentValidator
from tmis.document_intelligence.ingestion.virus_scan import NullVirusScanner
from tmis.document_intelligence.knowledge.builder import KnowledgeGraphBuilder
from tmis.document_intelligence.knowledge.in_memory_graph import InMemoryKnowledgeGraph
from tmis.document_intelligence.knowledge.ports import KnowledgeGraphPort
from tmis.document_intelligence.layout.heuristic_analyzer import HeuristicLayoutAnalyzer
from tmis.document_intelligence.layout.ports import LayoutAnalyzerPort
from tmis.document_intelligence.metadata.extractor import DefaultMetadataExtractor
from tmis.document_intelligence.metadata.ports import MetadataExtractorPort
from tmis.document_intelligence.ocr.language_detector import HeuristicLanguageDetector
from tmis.document_intelligence.ocr.ports import LanguageDetectorPort
from tmis.document_intelligence.ocr.registry import OcrEngineRegistry
from tmis.document_intelligence.schemas.document import ProcessingStatus
from tmis.document_intelligence.schemas.record import DocumentRecord
from tmis.document_intelligence.storage.in_memory_store import InMemoryDocumentStore
from tmis.document_intelligence.storage.ports import DocumentStorePort
from tmis.document_intelligence.timeline.builder import ChronologicalTimelineBuilder
from tmis.document_intelligence.timeline.ports import TimelineBuilderPort

T = TypeVar("T")

_LOGGER_NAME = "tmis.document_intelligence.pipeline"


class DocumentIntelligencePipeline:
    """Orchestrates the full Document Intelligence pipeline:

    Document -> Validation -> Virus Scan -> Ingestion -> OCR -> Language
    detection -> Layout detection -> Classification -> Metadata extraction
    -> Entity extraction -> Timeline construction -> Chunking ->
    Embeddings -> Knowledge graph update -> Storage -> `DocumentProcessed`

    Every dependency is injected behind a port with a sensible default, so
    `DocumentIntelligencePipeline()` works out of the box (see
    docs/14-document-intelligence.md). Each stage's duration, success and
    any error are recorded via `PipelineEvaluator`, and events are
    published on the Sprint 2 `EventBus`.
    """

    def __init__(
        self,
        *,
        event_bus: EventBus | None = None,
        validator: DocumentValidator | None = None,
        virus_scanner: VirusScanPort | None = None,
        ingestion_registry: IngestionRegistry | None = None,
        ocr_registry: OcrEngineRegistry | None = None,
        language_detector: LanguageDetectorPort | None = None,
        layout_analyzer: LayoutAnalyzerPort | None = None,
        classifier: ClassifierPort | None = None,
        metadata_extractor: MetadataExtractorPort | None = None,
        entity_extractor: EntityExtractorPort | None = None,
        timeline_builder: TimelineBuilderPort | None = None,
        chunker: DocumentChunkerPort | None = None,
        embedding_bridge: DocumentEmbeddingBridge | None = None,
        knowledge_graph: KnowledgeGraphPort | None = None,
        knowledge_builder: KnowledgeGraphBuilder | None = None,
        document_store: DocumentStorePort | None = None,
        evaluator: PipelineEvaluator | None = None,
    ) -> None:
        self.event_bus = event_bus or EventBus()
        self.validator = validator or DocumentValidator()
        self.virus_scanner: VirusScanPort = virus_scanner or NullVirusScanner()
        self.ingestion_registry = ingestion_registry or IngestionRegistry()
        self.ocr_registry = ocr_registry or OcrEngineRegistry()
        self.language_detector: LanguageDetectorPort = (
            language_detector or HeuristicLanguageDetector()
        )
        self.layout_analyzer: LayoutAnalyzerPort = layout_analyzer or HeuristicLayoutAnalyzer()
        self.classifier: ClassifierPort = classifier or KeywordClassifier()
        self.metadata_extractor: MetadataExtractorPort = (
            metadata_extractor or DefaultMetadataExtractor()
        )
        self.entity_extractor: EntityExtractorPort = entity_extractor or RegexEntityExtractor()
        self.timeline_builder: TimelineBuilderPort = (
            timeline_builder or ChronologicalTimelineBuilder()
        )
        self.chunker: DocumentChunkerPort = chunker or StructuralChunker()
        self.embedding_bridge = embedding_bridge or DocumentEmbeddingBridge()
        self.knowledge_graph: KnowledgeGraphPort = knowledge_graph or InMemoryKnowledgeGraph()
        self.knowledge_builder = knowledge_builder or KnowledgeGraphBuilder()
        self.document_store: DocumentStorePort = document_store or InMemoryDocumentStore()
        self.evaluator = evaluator or PipelineEvaluator()
        self._logger = get_logger(_LOGGER_NAME)

    async def process(
        self,
        filename: str,
        content_type: str,
        raw_bytes: bytes,
        *,
        document_id: str | None = None,
        source: str = "upload",
        case_id: str | None = None,
        firm_id: str | None = None,
    ) -> DocumentRecord:
        document_id = document_id or str(uuid.uuid4())
        run_id = uuid.uuid4()
        stage_metrics: list[StageMetric] = []
        pipeline_start = time.perf_counter()

        def stage(name: str, fn: Callable[[], T]) -> T:
            start = time.perf_counter()
            try:
                result = fn()
            except Exception as exc:
                duration_ms = (time.perf_counter() - start) * 1000
                stage_metrics.append(
                    StageMetric(stage=name, duration_ms=duration_ms, success=False, error=str(exc))
                )
                self._logger.error(
                    "document_intelligence_stage_failed",
                    stage=name,
                    document_id=document_id,
                    error=str(exc),
                )
                raise
            duration_ms = (time.perf_counter() - start) * 1000
            stage_metrics.append(StageMetric(stage=name, duration_ms=duration_ms, success=True))
            self._logger.info(
                "document_intelligence_stage_completed",
                stage=name,
                document_id=document_id,
                duration_ms=duration_ms,
            )
            return result

        async def stage_async(name: str, fn: Callable[[], Awaitable[T]]) -> T:
            start = time.perf_counter()
            try:
                result = await fn()
            except Exception as exc:
                duration_ms = (time.perf_counter() - start) * 1000
                stage_metrics.append(
                    StageMetric(stage=name, duration_ms=duration_ms, success=False, error=str(exc))
                )
                self._logger.error(
                    "document_intelligence_stage_failed",
                    stage=name,
                    document_id=document_id,
                    error=str(exc),
                )
                raise
            duration_ms = (time.perf_counter() - start) * 1000
            stage_metrics.append(StageMetric(stage=name, duration_ms=duration_ms, success=True))
            self._logger.info(
                "document_intelligence_stage_completed",
                stage=name,
                document_id=document_id,
                duration_ms=duration_ms,
            )
            return result

        await self.event_bus.publish(
            DocumentUploaded(
                workflow_id=run_id, document_id=document_id, filename=filename, case_id=case_id
            )
        )

        stage("validation", lambda: self.validator.validate(filename, raw_bytes))
        stage("virus_scan", lambda: self.virus_scanner.scan(filename, raw_bytes))
        ingested = stage(
            "ingestion",
            lambda: self.ingestion_registry.parse(document_id, filename, content_type, raw_bytes),
        )

        ocr_result = stage("ocr", lambda: self.ocr_registry.extract_text(ingested))
        await self.event_bus.publish(
            OCRCompleted(
                workflow_id=run_id, document_id=document_id, confidence=ocr_result.confidence
            )
        )

        language = stage(
            "language_detection", lambda: self.language_detector.detect(ocr_result.text)
        )

        layout_blocks = stage("layout", lambda: self.layout_analyzer.analyze(ocr_result.text))
        await self.event_bus.publish(
            LayoutDetected(
                workflow_id=run_id, document_id=document_id, block_count=len(layout_blocks)
            )
        )

        classification = stage("classification", lambda: self.classifier.classify(ocr_result.text))

        metadata = stage(
            "metadata",
            lambda: self.metadata_extractor.extract(
                ingested, ocr_result, language=language, source=source
            ),
        )
        await self.event_bus.publish(MetadataExtracted(workflow_id=run_id, document_id=document_id))

        entities = stage("entities", lambda: self.entity_extractor.extract(ocr_result.text))
        await self.event_bus.publish(
            EntitiesExtracted(
                workflow_id=run_id, document_id=document_id, entity_count=len(entities)
            )
        )

        timeline_events = stage(
            "timeline", lambda: self.timeline_builder.build(document_id, ocr_result.text, entities)
        )
        await self.event_bus.publish(
            TimelineBuilt(
                workflow_id=run_id, document_id=document_id, event_count=len(timeline_events)
            )
        )

        chunks = stage(
            "chunking", lambda: self.chunker.chunk(document_id, ocr_result.text, layout_blocks)
        )

        await stage_async("embeddings", lambda: self.embedding_bridge.embed_and_index(chunks))
        await self.event_bus.publish(
            EmbeddingsCreated(workflow_id=run_id, document_id=document_id, chunk_count=len(chunks))
        )

        stage(
            "knowledge",
            lambda: self.knowledge_builder.update(
                self.knowledge_graph,
                document_id=document_id,
                filename=filename,
                layout_blocks=layout_blocks,
                entities=entities,
                timeline_events=timeline_events,
                chunks=chunks,
            ),
        )
        await self.event_bus.publish(
            KnowledgeUpdated(
                workflow_id=run_id,
                document_id=document_id,
                node_count=getattr(self.knowledge_graph, "node_count", 0),
            )
        )

        record = DocumentRecord(
            document_id=document_id,
            filename=filename,
            status=ProcessingStatus.PROCESSED,
            raw_bytes=raw_bytes,
            ocr_text=ocr_result.text,
            layout_blocks=layout_blocks,
            classification=classification,
            metadata=metadata,
            entities=entities,
            timeline_events=timeline_events,
            chunk_ids=[chunk.id for chunk in chunks],
        )
        stage("storage", lambda: self.document_store.save(record))

        total_duration_ms = (time.perf_counter() - pipeline_start) * 1000
        self.evaluator.record(
            PipelineMetrics(
                document_id=document_id,
                total_duration_ms=total_duration_ms,
                stage_metrics=tuple(stage_metrics),
                ocr_confidence=ocr_result.confidence,
                entity_count=len(entities),
                chunk_count=len(chunks),
                knowledge_node_count=getattr(self.knowledge_graph, "node_count", 0),
            )
        )

        await self.event_bus.publish(
            DocumentProcessed(
                workflow_id=run_id,
                document_id=document_id,
                success=True,
                case_id=case_id,
                firm_id=firm_id,
            )
        )
        return record
