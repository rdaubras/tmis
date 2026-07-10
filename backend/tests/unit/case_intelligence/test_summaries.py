import pytest

from tmis.ai.schemas.provider import ModelResponse
from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.case_intelligence.issues.schemas import IssueStatus, LegalIssue
from tmis.case_intelligence.summaries.generator import CaseSummaryGenerator
from tmis.case_intelligence.timeline.schemas import CaseTimelineEntry, TimelineInconsistency


class _FakeKernel:
    def __init__(self) -> None:
        self.last_prompt: str | None = None

    async def complete(self, prompt: str) -> ModelResponse:
        self.last_prompt = prompt
        return ModelResponse(text=f"[fake] {prompt[:20]}", provider="fake", model="fake")


@pytest.mark.asyncio
async def test_generate_calls_kernel_complete_for_executive_summary() -> None:
    kernel = _FakeKernel()
    profile = CaseProfile(case_id="case-1", title="Dupont c. ACME")

    summary = await CaseSummaryGenerator(kernel).generate(profile)

    assert kernel.last_prompt is not None
    assert summary.executive_summary.startswith("[fake]")


@pytest.mark.asyncio
async def test_chronological_summary_lists_timeline_entries() -> None:
    profile = CaseProfile(case_id="case-1", title="Test")
    profile.timeline = [
        CaseTimelineEntry(
            date="12 janvier 2019", description="Signature", document_ids=(), confidence=0.6
        )
    ]
    summary = await CaseSummaryGenerator(_FakeKernel()).generate(profile)
    assert "12 janvier 2019" in summary.chronological_summary


@pytest.mark.asyncio
async def test_chronological_summary_handles_empty_timeline() -> None:
    profile = CaseProfile(case_id="case-1", title="Test")
    summary = await CaseSummaryGenerator(_FakeKernel()).generate(profile)
    assert "Aucun événement" in summary.chronological_summary


@pytest.mark.asyncio
async def test_case_status_reflects_open_issues() -> None:
    profile = CaseProfile(case_id="case-1", title="Test")
    profile.legal_issues = [LegalIssue(id="i1", description="Q1")]
    summary = await CaseSummaryGenerator(_FakeKernel()).generate(profile)
    assert "1 question" in summary.case_status


@pytest.mark.asyncio
async def test_case_status_deleted_case() -> None:
    profile = CaseProfile(case_id="case-1", title="Test", is_deleted=True)
    summary = await CaseSummaryGenerator(_FakeKernel()).generate(profile)
    assert summary.case_status == "Dossier clôturé"


@pytest.mark.asyncio
async def test_open_points_include_resolved_issues_only_when_open() -> None:
    profile = CaseProfile(case_id="case-1", title="Test")
    profile.legal_issues = [
        LegalIssue(id="i1", description="Ouverte"),
        LegalIssue(id="i2", description="Résolue", status=IssueStatus.RESOLVED),
    ]
    summary = await CaseSummaryGenerator(_FakeKernel()).generate(profile)
    assert "Ouverte" in summary.open_points
    assert "Résolue" not in summary.open_points


@pytest.mark.asyncio
async def test_open_points_include_timeline_inconsistencies() -> None:
    profile = CaseProfile(case_id="case-1", title="Test")
    entry = CaseTimelineEntry(
        date="1 janvier 2020", description="A", document_ids=(), confidence=0.6
    )
    profile.timeline_inconsistencies = [
        TimelineInconsistency(date="1 janvier 2020", entries=(entry,))
    ]
    summary = await CaseSummaryGenerator(_FakeKernel()).generate(profile)
    assert any("1 janvier 2020" in point for point in summary.open_points)


@pytest.mark.asyncio
async def test_documentary_summary_counts_documents_facts_and_actors() -> None:
    profile = CaseProfile(case_id="case-1", title="Test")
    profile.document_ids = {"doc-1", "doc-2"}
    summary = await CaseSummaryGenerator(_FakeKernel()).generate(profile)
    assert "2 document" in summary.documentary_summary
