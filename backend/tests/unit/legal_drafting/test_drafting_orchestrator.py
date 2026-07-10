import pytest

from tmis.ai.schemas.provider import ModelResponse
from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.case_intelligence.facts.schemas import Fact
from tmis.legal_drafting.documents.orchestrator import DocumentOrchestrator
from tmis.legal_drafting.documents.schemas import DraftWorkflowStatus
from tmis.legal_drafting.export.schemas import ExportFormat
from tmis.legal_drafting.templates.schemas import DocumentType
from tmis.legal_drafting.validation.schemas import DraftDecision
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis
from tmis.legal_reasoning.reasoner.schemas import ReasoningSession
from tmis.legal_research.search.schemas import ResearchResponse, ResearchResult


class _FakeCasePort:
    def __init__(self, profile: CaseProfile | None) -> None:
        self._profile = profile

    def get_profile(self, case_id: str) -> CaseProfile | None:
        return self._profile


class _FakeResearchPort:
    def __init__(self, results: list[ResearchResult]) -> None:
        self._results = results

    async def search(self, query: str, *, case_id: str | None = None) -> ResearchResponse:
        return ResearchResponse(
            search_id="search-1", query=query, results=tuple(self._results),
            connectors_used=("codes",), duration_ms=1.0,
        )


class _FakeReasoningPort:
    def __init__(self, session: ReasoningSession) -> None:
        self._session = session
        self._sessions = {session.id: session}

    async def reason(self, question: str, *, case_id: str | None = None) -> ReasoningSession:
        return self._session

    def get_session(self, session_id: str) -> ReasoningSession | None:
        return self._sessions.get(session_id)


class _FakeKernel:
    def __init__(self) -> None:
        self._call_count = 0

    async def complete(self, prompt: str) -> ModelResponse:
        self._call_count += 1
        return ModelResponse(
            text=f"[genere #{self._call_count}] {prompt[:15]}", provider="fake", model="fake"
        )


def _result() -> ResearchResult:
    return ResearchResult(
        id="r1", title="Code civil", excerpt="excerpt", connector="codes",
        document_type="code", reference="1240", date="2020-01-01", final_score=0.8,
    )


def _reasoning_session() -> ReasoningSession:
    hypothesis = Hypothesis(id="h1", description="Hypothèse test")
    return ReasoningSession(id="session-1", question="q", case_id=None, hypotheses=[hypothesis])


def _orchestrator(profile: CaseProfile | None = None) -> DocumentOrchestrator:
    return DocumentOrchestrator(
        kernel=_FakeKernel(),
        case_port=_FakeCasePort(profile),
        research_port=_FakeResearchPort([_result()]),
        reasoning_port=_FakeReasoningPort(_reasoning_session()),
    )


@pytest.mark.asyncio
async def test_create_draft_produces_a_document_with_all_sections() -> None:
    orchestrator = _orchestrator()
    document = await orchestrator.create_draft(DocumentType.CONSULTATION)

    assert document.is_draft is True
    assert document.status == DraftWorkflowStatus.UNDER_REVIEW
    assert [s.key for s in document.sections] == [
        "header", "context", "facts", "legal_discussion", "recommendations",
        "conclusion", "signature",
    ]


@pytest.mark.asyncio
async def test_create_draft_grounds_facts_section_in_case_facts() -> None:
    fact = Fact(id="f1", description="Le contrat a été rompu.", confidence=0.8)
    profile = CaseProfile(case_id="case-1", title="Test", facts=[fact])
    orchestrator = _orchestrator(profile=profile)

    document = await orchestrator.create_draft(
        DocumentType.CONSULTATION, case_id="case-1", question="Une question ?"
    )

    facts_section = next(s for s in document.sections if s.key == "facts")
    assert facts_section.paragraphs[0].fact_ids == ("f1",)


@pytest.mark.asyncio
async def test_create_draft_attaches_citations_for_grounded_paragraphs() -> None:
    orchestrator = _orchestrator()
    document = await orchestrator.create_draft(
        DocumentType.CONSULTATION, question="Une question ?"
    )
    assert document.citations
    assert all(c.document_id == document.id for c in document.citations)


@pytest.mark.asyncio
async def test_create_draft_records_history_and_a_version() -> None:
    orchestrator = _orchestrator()
    document = await orchestrator.create_draft(DocumentType.CONSULTATION)

    assert len(orchestrator.history(document.id)) == 1
    assert len(orchestrator.list_versions(document.id)) == 1


@pytest.mark.asyncio
async def test_regenerate_section_keeps_the_section_id() -> None:
    orchestrator = _orchestrator()
    document = await orchestrator.create_draft(DocumentType.CONSULTATION)
    original_section = next(s for s in document.sections if s.key == "context")
    original_id = original_section.id

    updated = await orchestrator.regenerate_section(document.id, "context")

    new_section = next(s for s in updated.sections if s.key == "context")
    assert new_section.id == original_id
    assert len(orchestrator.list_versions(document.id)) == 2


@pytest.mark.asyncio
async def test_regenerate_section_unknown_key_raises() -> None:
    orchestrator = _orchestrator()
    document = await orchestrator.create_draft(DocumentType.CONSULTATION)
    with pytest.raises(ValueError, match="Unknown section"):
        await orchestrator.regenerate_section(document.id, "does-not-exist")


@pytest.mark.asyncio
async def test_regenerate_paragraph_keeps_the_paragraph_id() -> None:
    orchestrator = _orchestrator()
    document = await orchestrator.create_draft(DocumentType.CONSULTATION)
    section = next(s for s in document.sections if s.key == "context")
    paragraph_id = section.paragraphs[0].id

    updated = await orchestrator.regenerate_paragraph(document.id, "context", paragraph_id)

    new_section = next(s for s in updated.sections if s.key == "context")
    assert new_section.paragraphs[0].id == paragraph_id


@pytest.mark.asyncio
async def test_compare_versions_detects_regeneration_changes() -> None:
    orchestrator = _orchestrator()
    document = await orchestrator.create_draft(DocumentType.CONSULTATION)
    await orchestrator.regenerate_section(document.id, "context")

    diff = orchestrator.compare_versions(document.id, 1, 2)

    context_section = next(s for s in document.sections if s.key == "context")
    assert context_section.paragraphs[0].id in diff.changed_paragraph_ids


@pytest.mark.asyncio
async def test_restore_version_reverts_a_regenerated_section() -> None:
    orchestrator = _orchestrator()
    document = await orchestrator.create_draft(DocumentType.CONSULTATION)
    original_text = next(s for s in document.sections if s.key == "header").paragraphs[0].text

    await orchestrator.regenerate_section(document.id, "context")
    restored = orchestrator.restore_version(document.id, 1, "avocat")

    restored_header = next(s for s in restored.sections if s.key == "header")
    assert restored_header.paragraphs[0].text == original_text


@pytest.mark.asyncio
async def test_validate_approved_never_changes_is_draft() -> None:
    orchestrator = _orchestrator()
    document = await orchestrator.create_draft(DocumentType.CONSULTATION)

    orchestrator.validate(document.id, DraftDecision.APPROVED, "avocat@cabinet.fr")

    assert document.is_draft is True
    assert document.status == DraftWorkflowStatus.LAWYER_APPROVED


@pytest.mark.asyncio
async def test_validate_rejected_updates_status() -> None:
    orchestrator = _orchestrator()
    document = await orchestrator.create_draft(DocumentType.CONSULTATION)

    orchestrator.validate(document.id, DraftDecision.REJECTED, "avocat@cabinet.fr", comment="Non")

    assert document.status == DraftWorkflowStatus.REJECTED
    assert len(orchestrator.list_validations(document.id)) == 1


@pytest.mark.asyncio
async def test_export_returns_bytes_for_every_format() -> None:
    orchestrator = _orchestrator()
    document = await orchestrator.create_draft(DocumentType.CONSULTATION)

    for export_format in (ExportFormat.HTML, ExportFormat.DOCX, ExportFormat.PDF):
        result = orchestrator.export(document.id, export_format)
        assert result.content
        assert result.format == export_format


@pytest.mark.asyncio
async def test_review_returns_findings_stored_on_the_document() -> None:
    orchestrator = _orchestrator()
    document = await orchestrator.create_draft(DocumentType.CONSULTATION)
    assert orchestrator.review(document.id) == document.review_findings


@pytest.mark.asyncio
async def test_get_document_returns_none_for_unknown_id() -> None:
    assert _orchestrator().get_document("unknown") is None
