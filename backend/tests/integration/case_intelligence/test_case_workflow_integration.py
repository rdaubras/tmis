import pytest

from tmis.ai.events.events import (
    CaseCreated,
    CaseIndexed,
    CaseUpdated,
    EvidenceUpdated,
    FactsUpdated,
    IssueDetected,
    TimelineUpdated,
)
from tmis.ai.kernel import TMISKernel
from tmis.case_intelligence.workflow.case_workflow import CaseIntelligenceWorkflow
from tmis.document_intelligence.pipeline.document_pipeline import DocumentIntelligencePipeline

_CONTRACT_TEXT = (
    "CONTRAT DE BAIL COMMERCIAL\n\n"
    "Signé le 12 janvier 2019 par Maître Jean Dupont et la société ACME SARL.\n\n"
    "Le loyer mensuel est de 1500 EUR."
)
_AMENDMENT_TEXT = (
    "AVENANT AU CONTRAT\n\n"
    "Le 12 janvier 2019, résiliation anticipée notifiée par Maître Jean Dupont."
)


def _wire() -> tuple[DocumentIntelligencePipeline, CaseIntelligenceWorkflow]:
    kernel = TMISKernel()
    pipeline = DocumentIntelligencePipeline(event_bus=kernel.event_bus)
    workflow = CaseIntelligenceWorkflow(
        document_store=pipeline.document_store, event_bus=kernel.event_bus
    )
    return pipeline, workflow


@pytest.mark.asyncio
async def test_processing_a_document_with_a_case_id_creates_the_case_automatically() -> None:
    pipeline, workflow = _wire()

    await pipeline.process("bail.txt", "text/plain", _CONTRACT_TEXT.encode(), case_id="case-1")

    profile = workflow.case_store.get("case-1")
    assert profile is not None
    assert len(profile.document_ids) == 1
    assert len(profile.actors) == 2
    assert len(profile.facts) == 1


@pytest.mark.asyncio
async def test_processing_a_document_without_a_case_id_does_not_touch_any_case() -> None:
    pipeline, workflow = _wire()

    await pipeline.process("bail.txt", "text/plain", _CONTRACT_TEXT.encode())

    assert workflow.case_store.list_ids() == []


@pytest.mark.asyncio
async def test_second_document_merges_actors_and_flags_contradiction() -> None:
    pipeline, workflow = _wire()

    await pipeline.process("bail.txt", "text/plain", _CONTRACT_TEXT.encode(), case_id="case-1")
    await pipeline.process(
        "avenant.txt", "text/plain", _AMENDMENT_TEXT.encode(), case_id="case-1"
    )

    profile = workflow.case_store.get("case-1")
    assert profile is not None
    assert len(profile.document_ids) == 2
    # "Maître Jean Dupont" is mentioned in both documents -> merged, not duplicated.
    assert len(profile.actors) == 2
    assert len(profile.timeline_inconsistencies) == 1
    assert any("Incohérence temporelle" in issue.description for issue in profile.legal_issues)


@pytest.mark.asyncio
async def test_case_events_are_published_alongside_document_events() -> None:
    pipeline, workflow = _wire()

    await pipeline.process("bail.txt", "text/plain", _CONTRACT_TEXT.encode(), case_id="case-1")

    event_types = {type(e) for e in workflow.event_bus.history}
    assert CaseCreated in event_types
    assert CaseUpdated in event_types
    assert FactsUpdated in event_types
    assert TimelineUpdated in event_types
    assert EvidenceUpdated in event_types
    assert CaseIndexed in event_types


@pytest.mark.asyncio
async def test_issue_detected_event_only_fires_when_issues_exist() -> None:
    pipeline, workflow = _wire()

    await pipeline.process("bail.txt", "text/plain", _CONTRACT_TEXT.encode(), case_id="case-1")
    first_run_events = [type(e) for e in workflow.event_bus.history]
    assert IssueDetected not in first_run_events

    await pipeline.process(
        "avenant.txt", "text/plain", _AMENDMENT_TEXT.encode(), case_id="case-1"
    )
    all_events = [type(e) for e in workflow.event_bus.history]
    assert IssueDetected in all_events


@pytest.mark.asyncio
async def test_ingest_document_can_be_called_directly_without_events() -> None:
    pipeline, workflow = _wire()

    record = await pipeline.process("bail.txt", "text/plain", _CONTRACT_TEXT.encode())
    # `case_id` was not passed to `process()`, so no case was auto-updated
    # above; call the workflow directly instead.
    profile = await workflow.ingest_document("case-2", record)

    assert profile.case_id == "case-2"
    assert record.document_id in profile.document_ids


@pytest.mark.asyncio
async def test_evaluator_records_metrics_for_every_ingested_document() -> None:
    pipeline, workflow = _wire()

    await pipeline.process("bail.txt", "text/plain", _CONTRACT_TEXT.encode(), case_id="case-1")
    await pipeline.process(
        "avenant.txt", "text/plain", _AMENDMENT_TEXT.encode(), case_id="case-1"
    )

    metrics = workflow.evaluator.for_case("case-1")
    assert len(metrics) == 2
    assert all(m.error_count == 0 for m in metrics)


@pytest.mark.asyncio
async def test_ai_history_records_one_entry_per_document() -> None:
    pipeline, workflow = _wire()

    await pipeline.process("bail.txt", "text/plain", _CONTRACT_TEXT.encode(), case_id="case-1")
    await pipeline.process(
        "avenant.txt", "text/plain", _AMENDMENT_TEXT.encode(), case_id="case-1"
    )

    profile = workflow.case_store.get("case-1")
    assert profile is not None
    assert len(profile.ai_history) == 2
