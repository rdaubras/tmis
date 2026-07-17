import time
import uuid
from datetime import UTC, datetime

from tmis.ai.evaluation.metrics import estimate_cost
from tmis.ai.schemas.provider import ModelResponse
from tmis.core.logging import get_logger
from tmis.legal_drafting.citations.engine import CitationEngine
from tmis.legal_drafting.citations.schemas import DraftCitation
from tmis.legal_drafting.documents.ports import (
    DocumentStorePort,
    DraftingCasePort,
    DraftingReasoningPort,
    DraftingResearchPort,
)
from tmis.legal_drafting.documents.schemas import Document, DraftingContext, DraftWorkflowStatus
from tmis.legal_drafting.documents.store import InMemoryDocumentStore
from tmis.legal_drafting.evaluation.evaluator import DraftEvaluator
from tmis.legal_drafting.evaluation.metrics import DraftMetrics
from tmis.legal_drafting.export.docx_exporter import DocxExporter
from tmis.legal_drafting.export.html_exporter import HtmlExporter
from tmis.legal_drafting.export.pdf_exporter import PdfExporter
from tmis.legal_drafting.export.ports import ExporterPort
from tmis.legal_drafting.export.schemas import ExportFormat, ExportResult
from tmis.legal_drafting.history.ports import DraftHistoryPort
from tmis.legal_drafting.history.schemas import DraftHistoryActionType, DraftHistoryEntry
from tmis.legal_drafting.history.store import InMemoryDraftHistory
from tmis.legal_drafting.paragraphs.engine import HeuristicParagraphEngine
from tmis.legal_drafting.paragraphs.ports import DraftingKernelPort
from tmis.legal_drafting.paragraphs.schemas import Paragraph
from tmis.legal_drafting.references.ports import ReferenceResolverPort
from tmis.legal_drafting.references.resolver import HeuristicReferenceResolver
from tmis.legal_drafting.review.engine import HeuristicReviewEngine
from tmis.legal_drafting.review.ports import ReviewEnginePort
from tmis.legal_drafting.review.schemas import ReviewFinding
from tmis.legal_drafting.sections.builder import DocumentBuilder
from tmis.legal_drafting.sections.schemas import Section
from tmis.legal_drafting.style.engine import StyleEngine
from tmis.legal_drafting.style.ports import StyleEnginePort, StyleProfileRegistryPort
from tmis.legal_drafting.style.registry import StyleProfileRegistry
from tmis.legal_drafting.templates.ports import TemplateRegistryPort
from tmis.legal_drafting.templates.registry import TemplateRegistry
from tmis.legal_drafting.templates.schemas import DocumentTemplate, DocumentType, TemplateSection
from tmis.legal_drafting.validation.ports import DraftValidationServicePort
from tmis.legal_drafting.validation.schemas import DraftDecision, DraftValidationRecord
from tmis.legal_drafting.validation.service import HumanInTheLoopService
from tmis.legal_drafting.versioning.ports import VersioningPort
from tmis.legal_drafting.versioning.schemas import DocumentVersion, VersionDiff
from tmis.legal_drafting.versioning.service import InMemoryVersioningService

_LOGGER_NAME = "tmis.legal_drafting.documents"


class _CostTrackingKernel:
    """Wraps `DraftingKernelPort` to accumulate token usage/provider for
    exactly one drafting operation, so `DraftEvaluator` can report an
    estimated cost without every leaf engine needing its own counter."""

    def __init__(self, kernel: DraftingKernelPort) -> None:
        self._kernel = kernel
        self.total_tokens = 0
        self.provider = "local"

    async def complete(self, prompt: str) -> ModelResponse:
        response = await self._kernel.complete(prompt)
        self.total_tokens += response.total_tokens
        self.provider = response.provider
        return response


class DocumentOrchestrator:
    """Pilots one full drafting run (see docs/28-legal-drafting.md):
    user request -> context analysis -> template selection -> section
    generation -> references -> coherence review -> draft creation ->
    publication (made available for the avocat's review — never a legal
    act). Every dependency is injected behind a port with a sensible
    default, matching the `ReasoningOrchestrator`/`ResearchOrchestrator`
    pattern from Sprints 5-6. It never produces anything but a draft.
    """

    def __init__(
        self,
        *,
        kernel: DraftingKernelPort,
        case_port: DraftingCasePort,
        research_port: DraftingResearchPort,
        reasoning_port: DraftingReasoningPort,
        template_registry: TemplateRegistryPort | None = None,
        style_registry: StyleProfileRegistryPort | None = None,
        style_engine: StyleEnginePort | None = None,
        reference_resolver: ReferenceResolverPort | None = None,
        citation_engine: CitationEngine | None = None,
        review_engine: ReviewEnginePort | None = None,
        validation_service: DraftValidationServicePort | None = None,
        versioning_service: VersioningPort | None = None,
        history: DraftHistoryPort | None = None,
        evaluator: DraftEvaluator | None = None,
        document_store: DocumentStorePort | None = None,
        exporters: dict[ExportFormat, ExporterPort] | None = None,
    ) -> None:
        self._kernel = kernel
        self._case_port = case_port
        self._research_port = research_port
        self._reasoning_port = reasoning_port
        self._template_registry: TemplateRegistryPort = template_registry or TemplateRegistry()
        self._style_registry: StyleProfileRegistryPort = style_registry or StyleProfileRegistry()
        self._style_engine: StyleEnginePort = style_engine or StyleEngine()
        self._reference_resolver: ReferenceResolverPort = (
            reference_resolver or HeuristicReferenceResolver()
        )
        self._citation_engine = citation_engine or CitationEngine()
        self._review_engine: ReviewEnginePort = review_engine or HeuristicReviewEngine()
        self._validation_service: DraftValidationServicePort = (
            validation_service or HumanInTheLoopService()
        )
        self._versioning_service: VersioningPort = versioning_service or InMemoryVersioningService()
        self._history: DraftHistoryPort = history or InMemoryDraftHistory()
        self._evaluator = evaluator or DraftEvaluator()
        self._document_store: DocumentStorePort = document_store or InMemoryDocumentStore()
        self._exporters: dict[ExportFormat, ExporterPort] = exporters or {
            ExportFormat.HTML: HtmlExporter(),
            ExportFormat.DOCX: DocxExporter(),
            ExportFormat.PDF: PdfExporter(),
        }
        self._logger = get_logger(_LOGGER_NAME)

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------
    async def create_draft(
        self,
        document_type: DocumentType,
        *,
        case_id: str | None = None,
        question: str | None = None,
        reasoning_session_id: str | None = None,
        style_profile_id: str = "default",
        variables: dict[str, str] | None = None,
    ) -> Document:
        start = time.perf_counter()
        components_used: list[str] = ["templates"]

        template = self._template_registry.get_latest(document_type)

        context, resolved_reasoning_session_id = await self._analyze_context(
            case_id=case_id,
            question=question,
            reasoning_session_id=reasoning_session_id,
            style_profile_id=style_profile_id,
            variables=variables,
            components_used=components_used,
        )

        document_id = str(uuid.uuid4())
        tracking_kernel = _CostTrackingKernel(self._kernel)
        sections = await self._build_sections(
            template.sections, context, tracking_kernel, components_used
        )
        citations = self._build_citations(document_id, sections, context, components_used)
        findings = self._review_engine.review(
            sections, list(template.sections), context.reasoning_session
        )
        components_used.append("review")

        title = context.variables.get("title") or (
            f"{template.name} — {context.variables.get('client_name', 'Client')}"
        )
        document = Document(
            id=document_id,
            template_id=template.id,
            document_type=document_type,
            case_id=case_id,
            title=title,
            sections=sections,
            citations=citations,
            review_findings=findings,
            status=DraftWorkflowStatus.UNDER_REVIEW,
            source_question=question,
            reasoning_session_id=resolved_reasoning_session_id,
            style_profile_id=style_profile_id,
            variables=context.variables,
        )
        self._document_store.save(document)
        self._versioning_service.snapshot(document.id, document.sections, author="system")
        self._history.record(
            document.id,
            DraftHistoryActionType.CREATED,
            details=f"Brouillon généré et mis à disposition pour relecture ({template.id}).",
        )

        self._record_metrics(document, template, sections, citations, tracking_kernel, start)
        return document

    async def _analyze_context(
        self,
        *,
        case_id: str | None,
        question: str | None,
        reasoning_session_id: str | None,
        style_profile_id: str,
        variables: dict[str, str] | None,
        components_used: list[str],
    ) -> tuple[DraftingContext, str | None]:
        profile = self._case_port.get_profile(case_id) if case_id else None
        facts = list(profile.facts) if profile else []
        if profile is not None:
            components_used.append("case_intelligence")

        research_results = []
        if question:
            research_response = await self._research_port.search(question, case_id=case_id)
            research_results = list(research_response.results)
            components_used.append("legal_research")

        reasoning_session = None
        resolved_reasoning_session_id = reasoning_session_id
        if reasoning_session_id is not None:
            reasoning_session = self._reasoning_port.get_session(reasoning_session_id)
        elif question is not None:
            reasoning_session = await self._reasoning_port.reason(question, case_id=case_id)
            resolved_reasoning_session_id = reasoning_session.id
        if reasoning_session is not None:
            components_used.append("legal_reasoning")

        style_profile = self._style_registry.get(style_profile_id) or (
            self._style_registry.get_default()
        )
        context = DraftingContext(
            case_id=case_id,
            facts=facts,
            research_results=research_results,
            reasoning_session=reasoning_session,
            style_profile=style_profile,
            variables=dict(variables or {}),
        )
        return context, resolved_reasoning_session_id

    async def _build_sections(
        self,
        template_sections: tuple[TemplateSection, ...],
        context: DraftingContext,
        tracking_kernel: _CostTrackingKernel,
        components_used: list[str],
    ) -> list[Section]:
        paragraph_engine = HeuristicParagraphEngine(tracking_kernel, self._style_engine)
        builder = DocumentBuilder(paragraph_engine)
        components_used.append("paragraphs")
        return await builder.build_sections(
            list(template_sections),
            facts=context.facts,
            research_results=context.research_results,
            reasoning_session=context.reasoning_session,
            style_profile=context.style_profile,
            variables=context.variables,
        )

    def _build_citations(
        self,
        document_id: str,
        sections: list[Section],
        context: DraftingContext,
        components_used: list[str],
    ) -> list[DraftCitation]:
        citations: list[DraftCitation] = []
        for section in sections:
            for paragraph in section.paragraphs:
                references = self._reference_resolver.resolve(
                    paragraph,
                    facts=context.facts,
                    research_results=context.research_results,
                    reasoning_session=context.reasoning_session,
                )
                citations.extend(
                    self._citation_engine.build_for_paragraph(
                        document_id, section.id, paragraph, references
                    )
                )
        if citations:
            components_used.append("references")
            components_used.append("citations")
        return citations

    def _record_metrics(
        self,
        document: Document,
        template: DocumentTemplate,
        sections: list[Section],
        citations: list[DraftCitation],
        tracking_kernel: _CostTrackingKernel,
        start: float,
    ) -> None:
        duration_ms = (time.perf_counter() - start) * 1000
        paragraph_count = sum(len(s.paragraphs) for s in sections)
        estimated_cost = estimate_cost(tracking_kernel.provider, tracking_kernel.total_tokens)
        self._evaluator.record(
            DraftMetrics(
                document_id=document.id,
                duration_ms=duration_ms,
                components_used=("templates", "paragraphs", "references", "citations", "review"),
                paragraph_count=paragraph_count,
                reference_count=len(citations),
                estimated_cost_usd=estimated_cost,
                template_id=template.id,
            )
        )
        self._logger.info(
            "draft_created",
            document_id=document.id,
            duration_ms=duration_ms,
            paragraph_count=paragraph_count,
            reference_count=len(citations),
            estimated_cost_usd=estimated_cost,
            template_id=template.id,
        )

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------
    def get_document(self, document_id: str) -> Document | None:
        return self._document_store.get(document_id)

    def _require_document(self, document_id: str) -> Document:
        document = self._document_store.get(document_id)
        if document is None:
            raise ValueError(f"No draft found for {document_id!r}")
        return document

    def _require_template(self, template_id: str) -> DocumentTemplate:
        template = self._template_registry.get(template_id)
        if template is None:
            raise ValueError(f"Unknown template {template_id!r}")
        return template

    def _require_template_section(
        self, template: DocumentTemplate, section_key: str
    ) -> TemplateSection:
        for template_section in template.sections:
            if template_section.key == section_key:
                return template_section
        raise ValueError(f"Unknown section {section_key!r} for template {template.id!r}")

    def _require_section(self, document: Document, section_key: str) -> Section:
        for section in document.sections:
            if section.key == section_key:
                return section
        raise ValueError(f"Unknown section {section_key!r} for draft {document.id!r}")

    def _require_paragraph(self, section: Section, paragraph_id: str) -> tuple[int, Paragraph]:
        for index, paragraph in enumerate(section.paragraphs):
            if paragraph.id == paragraph_id:
                return index, paragraph
        raise ValueError(f"Unknown paragraph {paragraph_id!r} in section {section.key!r}")

    # ------------------------------------------------------------------
    # Independent regeneration
    # ------------------------------------------------------------------
    async def regenerate_section(self, document_id: str, section_key: str) -> Document:
        document = self._require_document(document_id)
        template = self._require_template(document.template_id)
        template_section = self._require_template_section(template, section_key)

        context, _ = await self._analyze_context(
            case_id=document.case_id,
            question=document.source_question,
            reasoning_session_id=document.reasoning_session_id,
            style_profile_id=document.style_profile_id,
            variables=document.variables,
            components_used=[],
        )
        tracking_kernel = _CostTrackingKernel(self._kernel)
        paragraph_engine = HeuristicParagraphEngine(tracking_kernel, self._style_engine)
        builder = DocumentBuilder(paragraph_engine)
        new_section = await builder.regenerate_section(
            template_section,
            facts=context.facts,
            research_results=context.research_results,
            reasoning_session=context.reasoning_session,
            style_profile=context.style_profile,
            variables=context.variables,
        )

        old_section = self._require_section(document, section_key)
        new_section.id = old_section.id
        # Preserve paragraph ids/order position-by-position so versioning
        # reports this as a *change* to existing paragraphs rather than
        # removing and adding new ones — regenerating a section keeps its
        # continuity, it doesn't replace it with an unrelated one.
        for old_paragraph, new_paragraph in zip(
            old_section.paragraphs, new_section.paragraphs, strict=False
        ):
            new_paragraph.id = old_paragraph.id
            new_paragraph.order = old_paragraph.order
        index = document.sections.index(old_section)
        document.sections[index] = new_section

        document.citations = [c for c in document.citations if c.section_id != old_section.id]
        document.citations.extend(self._build_citations(document.id, [new_section], context, []))
        document.review_findings = self._review_engine.review(
            document.sections, list(template.sections), context.reasoning_session
        )
        self._finalize_mutation(
            document,
            DraftHistoryActionType.SECTION_REGENERATED,
            f"Section {section_key!r} régénérée.",
        )
        return document

    async def regenerate_paragraph(
        self, document_id: str, section_key: str, paragraph_id: str
    ) -> Document:
        document = self._require_document(document_id)
        template = self._require_template(document.template_id)
        template_section = self._require_template_section(template, section_key)
        section = self._require_section(document, section_key)
        paragraph_index, paragraph = self._require_paragraph(section, paragraph_id)

        context, _ = await self._analyze_context(
            case_id=document.case_id,
            question=document.source_question,
            reasoning_session_id=document.reasoning_session_id,
            style_profile_id=document.style_profile_id,
            variables=document.variables,
            components_used=[],
        )
        tracking_kernel = _CostTrackingKernel(self._kernel)
        paragraph_engine = HeuristicParagraphEngine(tracking_kernel, self._style_engine)
        new_paragraph = await paragraph_engine.regenerate_one(
            paragraph,
            template_section,
            facts=context.facts,
            research_results=context.research_results,
            reasoning_session=context.reasoning_session,
            style_profile=context.style_profile,
            variables=context.variables,
        )
        section.paragraphs[paragraph_index] = new_paragraph

        document.citations = [c for c in document.citations if c.paragraph_id != paragraph_id]
        references = self._reference_resolver.resolve(
            new_paragraph,
            facts=context.facts,
            research_results=context.research_results,
            reasoning_session=context.reasoning_session,
        )
        document.citations.extend(
            self._citation_engine.build_for_paragraph(
                document.id, section.id, new_paragraph, references
            )
        )
        document.review_findings = self._review_engine.review(
            document.sections, list(template.sections), context.reasoning_session
        )
        self._finalize_mutation(
            document,
            DraftHistoryActionType.PARAGRAPH_REGENERATED,
            f"Paragraphe {paragraph_id!r} régénéré.",
        )
        return document

    def _finalize_mutation(
        self, document: Document, action: DraftHistoryActionType, details: str
    ) -> None:
        document.updated_at = datetime.now(UTC)
        self._document_store.save(document)
        self._versioning_service.snapshot(document.id, document.sections, author="system")
        self._history.record(document.id, action, details=details)

    # ------------------------------------------------------------------
    # Versioning
    # ------------------------------------------------------------------
    def list_versions(self, document_id: str) -> list[DocumentVersion]:
        return self._versioning_service.list_versions(document_id)

    def compare_versions(self, document_id: str, version_a: int, version_b: int) -> VersionDiff:
        return self._versioning_service.compare(document_id, version_a, version_b)

    def restore_version(self, document_id: str, version_number: int, author: str) -> Document:
        document = self._require_document(document_id)
        document.sections = self._versioning_service.restore(document_id, version_number)
        document.updated_at = datetime.now(UTC)
        self._document_store.save(document)
        self._versioning_service.snapshot(document.id, document.sections, author=author)
        self._history.record(
            document.id,
            DraftHistoryActionType.VERSION_RESTORED,
            author=author,
            details=f"Version {version_number} restaurée.",
        )
        return document

    # ------------------------------------------------------------------
    # Human in the loop
    # ------------------------------------------------------------------
    def validate(
        self, document_id: str, decision: DraftDecision, author: str, comment: str | None = None
    ) -> DraftValidationRecord:
        document = self._require_document(document_id)
        record = self._validation_service.record(document_id, decision, author, comment)
        if decision == DraftDecision.APPROVED:
            document.status = DraftWorkflowStatus.LAWYER_APPROVED
        elif decision == DraftDecision.REJECTED:
            document.status = DraftWorkflowStatus.REJECTED
        self._document_store.save(document)
        self._history.record(
            document.id, DraftHistoryActionType.VALIDATED, author=author, details=decision.value
        )
        return record

    def list_validations(self, document_id: str) -> list[DraftValidationRecord]:
        return self._validation_service.list_for_document(document_id)

    # ------------------------------------------------------------------
    # Review / history
    # ------------------------------------------------------------------
    def review(self, document_id: str) -> list[ReviewFinding]:
        return self._require_document(document_id).review_findings

    def history(self, document_id: str) -> list[DraftHistoryEntry]:
        self._require_document(document_id)
        return self._history.list_for_document(document_id)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def export(self, document_id: str, export_format: ExportFormat) -> ExportResult:
        document = self._require_document(document_id)
        exporter = self._exporters.get(export_format)
        if exporter is None:
            raise ValueError(f"No exporter registered for {export_format!r}")
        result = exporter.export(document)
        self._history.record(
            document.id, DraftHistoryActionType.EXPORTED, details=export_format.value
        )
        return result
