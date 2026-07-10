import time
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import TypeVar

from tmis.ai.events.bus import EventBus
from tmis.ai.events.events import (
    CaseCreated,
    CaseIndexed,
    CaseSummarized,
    CaseUpdated,
    DocumentProcessed,
    EvidenceUpdated,
    FactsUpdated,
    IssueDetected,
    TimelineUpdated,
)
from tmis.ai.kernel import TMISKernel
from tmis.case_intelligence.actors.merger import ActorMerger
from tmis.case_intelligence.actors.ports import ActorMergerPort
from tmis.case_intelligence.cases.in_memory_store import InMemoryCaseStore
from tmis.case_intelligence.cases.ports import CaseStorePort
from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.case_intelligence.evaluation.evaluator import CaseEvaluator
from tmis.case_intelligence.evaluation.metrics import CaseUpdateMetrics, StepMetric
from tmis.case_intelligence.evidence.linker import EvidenceLinker
from tmis.case_intelligence.evidence.ports import EvidenceLinkerPort
from tmis.case_intelligence.facts.engine import FactEngine
from tmis.case_intelligence.facts.ports import FactEnginePort
from tmis.case_intelligence.issues.heuristic_detector import HeuristicIssueDetector
from tmis.case_intelligence.issues.ports import IssueDetectorPort
from tmis.case_intelligence.knowledge.aggregator import CaseKnowledgeAggregator
from tmis.case_intelligence.relationships.in_memory_graph import InMemoryCaseGraph
from tmis.case_intelligence.relationships.ports import CaseGraphPort
from tmis.case_intelligence.search.engine import CaseSearchEngine
from tmis.case_intelligence.search.ports import CaseSearchPort
from tmis.case_intelligence.summaries.generator import CaseSummaryGenerator
from tmis.case_intelligence.summaries.ports import SummaryGeneratorPort
from tmis.case_intelligence.summaries.schemas import CaseSummary
from tmis.case_intelligence.timeline.engine import CaseTimelineEngine
from tmis.case_intelligence.timeline.ports import TimelineConsolidatorPort
from tmis.core.logging import get_logger
from tmis.document_intelligence.schemas.record import DocumentRecord
from tmis.document_intelligence.storage.ports import DocumentStorePort

T = TypeVar("T")

_LOGGER_NAME = "tmis.case_intelligence.workflow"


class CaseIntelligenceWorkflow:
    """Makes a case "living": every time a document finishes processing
    (`DocumentProcessed`, published by `DocumentIntelligencePipeline` on
    the shared `EventBus`), the case's actors, facts, timeline, evidence,
    issues, knowledge graph and search index are all updated
    automatically, and the corresponding CIE events are published (see
    docs/19-case-intelligence.md).

    Every dependency is injected behind a port with a sensible default,
    matching the `TMISKernel`/`DocumentIntelligencePipeline` pattern from
    Sprints 2-3. `document_store` must be provided (and share the same
    `event_bus` as the `DocumentIntelligencePipeline` it is paired with)
    for the automatic, event-driven flow to work — `ingest_document()` can
    always be called directly otherwise.
    """

    def __init__(
        self,
        *,
        case_store: CaseStorePort | None = None,
        document_store: DocumentStorePort | None = None,
        event_bus: EventBus | None = None,
        actor_merger: ActorMergerPort | None = None,
        fact_engine: FactEnginePort | None = None,
        evidence_linker: EvidenceLinkerPort | None = None,
        timeline_engine: TimelineConsolidatorPort | None = None,
        issue_detector: IssueDetectorPort | None = None,
        knowledge_graph: CaseGraphPort | None = None,
        knowledge_aggregator: CaseKnowledgeAggregator | None = None,
        search_engine: CaseSearchPort | None = None,
        summary_generator: SummaryGeneratorPort | None = None,
        evaluator: CaseEvaluator | None = None,
        auto_subscribe: bool = True,
    ) -> None:
        self.case_store: CaseStorePort = case_store or InMemoryCaseStore()
        self.document_store = document_store
        self.event_bus = event_bus or EventBus()
        self.actor_merger: ActorMergerPort = actor_merger or ActorMerger()
        self.fact_engine: FactEnginePort = fact_engine or FactEngine()
        self.evidence_linker: EvidenceLinkerPort = evidence_linker or EvidenceLinker()
        self.timeline_engine: TimelineConsolidatorPort = timeline_engine or CaseTimelineEngine()
        self.issue_detector: IssueDetectorPort = issue_detector or HeuristicIssueDetector()
        self.knowledge_graph: CaseGraphPort = knowledge_graph or InMemoryCaseGraph()
        self.knowledge_aggregator = knowledge_aggregator or CaseKnowledgeAggregator()
        self.search_engine: CaseSearchPort = search_engine or CaseSearchEngine()
        self.summary_generator: SummaryGeneratorPort = summary_generator or CaseSummaryGenerator(
            TMISKernel()
        )
        self.evaluator = evaluator or CaseEvaluator()
        self._logger = get_logger(_LOGGER_NAME)

        if auto_subscribe:
            self.event_bus.subscribe(DocumentProcessed, self._on_document_processed)

    async def _on_document_processed(self, event: DocumentProcessed) -> None:
        if not event.success or event.case_id is None or self.document_store is None:
            return
        record = self.document_store.get(event.document_id)
        if record is None:
            return
        await self.ingest_document(event.case_id, record)

    async def ingest_document(self, case_id: str, record: DocumentRecord) -> CaseProfile:
        """Runs the full living-case enrichment for one document (see
        docs/19-case-intelligence.md for the step-by-step flow)."""
        run_id = uuid.uuid4()
        step_metrics: list[StepMetric] = []
        start_total = time.perf_counter()

        def step(name: str, fn: Callable[[], T]) -> T:
            start = time.perf_counter()
            try:
                result = fn()
            except Exception as exc:
                duration_ms = (time.perf_counter() - start) * 1000
                step_metrics.append(
                    StepMetric(step=name, duration_ms=duration_ms, success=False, error=str(exc))
                )
                self._logger.error(
                    "case_intelligence_step_failed", step=name, case_id=case_id, error=str(exc)
                )
                raise
            duration_ms = (time.perf_counter() - start) * 1000
            step_metrics.append(StepMetric(step=name, duration_ms=duration_ms, success=True))
            self._logger.info(
                "case_intelligence_step_completed",
                step=name,
                case_id=case_id,
                duration_ms=duration_ms,
            )
            return result

        async def step_async(name: str, fn: Callable[[], Awaitable[T]]) -> T:
            start = time.perf_counter()
            try:
                result = await fn()
            except Exception as exc:
                duration_ms = (time.perf_counter() - start) * 1000
                step_metrics.append(
                    StepMetric(step=name, duration_ms=duration_ms, success=False, error=str(exc))
                )
                self._logger.error(
                    "case_intelligence_step_failed", step=name, case_id=case_id, error=str(exc)
                )
                raise
            duration_ms = (time.perf_counter() - start) * 1000
            step_metrics.append(StepMetric(step=name, duration_ms=duration_ms, success=True))
            self._logger.info(
                "case_intelligence_step_completed",
                step=name,
                case_id=case_id,
                duration_ms=duration_ms,
            )
            return result

        is_new_case = self.case_store.get(case_id) is None
        profile = self.case_store.get_or_create(case_id, title=case_id)
        if is_new_case:
            await self.event_bus.publish(CaseCreated(workflow_id=run_id, case_id=case_id))

        step("register_document", lambda: profile.document_ids.add(record.document_id))
        profile.actors = step(
            "update_actors",
            lambda: self.actor_merger.merge(profile.actors, record.entities, record.document_id),
        )
        profile.facts = step(
            "update_facts",
            lambda: self.fact_engine.ingest(
                profile.facts, record.timeline_events, record.document_id
            ),
        )
        profile.timeline = step(
            "update_timeline",
            lambda: self.timeline_engine.consolidate(profile.timeline, record.timeline_events),
        )
        profile.timeline_inconsistencies = step(
            "detect_temporal_inconsistencies",
            lambda: self.timeline_engine.detect_inconsistencies(profile.timeline),
        )
        profile.evidence_links = step(
            "update_evidence",
            lambda: [
                link for fact in profile.facts for link in self.evidence_linker.link(fact)
            ],
        )
        profile.legal_issues = step(
            "detect_issues", lambda: self.issue_detector.detect(profile)
        )
        step(
            "update_knowledge_graph",
            lambda: self.knowledge_aggregator.update(self.knowledge_graph, profile),
        )
        await step_async("reindex_search", lambda: self.search_engine.reindex(profile))

        profile.record_ai_action(f"Document {record.document_id} traité automatiquement.")
        profile.updated_at = datetime.now(UTC)
        step("save", lambda: self.case_store.save(profile))

        await self.event_bus.publish(
            CaseUpdated(workflow_id=run_id, case_id=case_id, document_id=record.document_id)
        )
        await self.event_bus.publish(
            FactsUpdated(workflow_id=run_id, case_id=case_id, fact_count=len(profile.facts))
        )
        await self.event_bus.publish(
            TimelineUpdated(
                workflow_id=run_id,
                case_id=case_id,
                entry_count=len(profile.timeline),
                inconsistency_count=len(profile.timeline_inconsistencies),
            )
        )
        await self.event_bus.publish(
            EvidenceUpdated(
                workflow_id=run_id,
                case_id=case_id,
                evidence_link_count=len(profile.evidence_links),
            )
        )
        if profile.legal_issues:
            await self.event_bus.publish(
                IssueDetected(
                    workflow_id=run_id, case_id=case_id, issue_count=len(profile.legal_issues)
                )
            )
        await self.event_bus.publish(CaseIndexed(workflow_id=run_id, case_id=case_id))

        total_duration_ms = (time.perf_counter() - start_total) * 1000
        self.evaluator.record(
            CaseUpdateMetrics(
                case_id=case_id,
                document_id=record.document_id,
                total_duration_ms=total_duration_ms,
                step_metrics=tuple(step_metrics),
            )
        )
        return profile

    async def summarize(self, case_id: str) -> CaseSummary:
        profile = self.case_store.get_or_create(case_id, title=case_id)
        summary = await self.summary_generator.generate(profile)
        await self.event_bus.publish(CaseSummarized(workflow_id=uuid.uuid4(), case_id=case_id))
        return summary
