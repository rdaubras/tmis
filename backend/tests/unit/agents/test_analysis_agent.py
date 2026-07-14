import uuid

import pytest

from tmis.agents.analysis_agent import AnalysisAgent
from tmis.agents.contracts import AgentInput, ConfidenceLevel
from tmis.ai_fabric.bootstrap import get_ai_intelligence_fabric
from tmis.ai_governance.bootstrap import get_ai_governance_platform
from tmis.case_intelligence.cases.in_memory_store import InMemoryCaseStore
from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.case_intelligence.timeline.schemas import CaseTimelineEntry, TimelineInconsistency
from tmis.document_intelligence.schemas.document import ProcessingStatus
from tmis.document_intelligence.schemas.entities import EntityType, ExtractedEntity
from tmis.document_intelligence.schemas.record import DocumentRecord
from tmis.document_intelligence.storage.in_memory_store import InMemoryDocumentStore


def _make_document(document_id: str = "doc-1") -> DocumentRecord:
    return DocumentRecord(
        document_id=document_id,
        filename="contrat-bail.pdf",
        status=ProcessingStatus.ENTITIES_EXTRACTED,
        raw_bytes=b"%PDF-1.4 fake",
        ocr_text="Contrat de bail entre Jean Dupont et Acme SARL, signe le 12 mars 2024.",
        entities=[
            ExtractedEntity(type=EntityType.PERSON, value="Jean Dupont", confidence=0.9),
            ExtractedEntity(type=EntityType.COMPANY, value="Acme SARL", confidence=0.85),
            ExtractedEntity(type=EntityType.DATE, value="2024-03-12", confidence=0.95),
            ExtractedEntity(type=EntityType.AMOUNT, value="1200 EUR", confidence=0.8),
        ],
    )


@pytest.mark.asyncio
async def test_analysis_agent_without_document_id_is_low_confidence() -> None:
    agent = AnalysisAgent()
    agent_input = AgentInput(task_id=uuid.uuid4(), case_id=None)

    output = await agent.run(agent_input)

    assert output.confidence == ConfidenceLevel.LOW
    assert any("document_id" in warning for warning in output.warnings)
    assert output.result["entities"] == {}


@pytest.mark.asyncio
async def test_analysis_agent_reports_missing_document() -> None:
    agent = AnalysisAgent(document_store=InMemoryDocumentStore())
    agent_input = AgentInput(
        task_id=uuid.uuid4(), case_id=None, context={"document_id": "missing-doc"}
    )

    output = await agent.run(agent_input)

    assert output.confidence == ConfidenceLevel.LOW
    assert any("missing-doc" in warning for warning in output.warnings)


@pytest.mark.asyncio
async def test_analysis_agent_extracts_entities_from_persisted_document() -> None:
    document_store = InMemoryDocumentStore()
    document = _make_document()
    document_store.save(document)
    agent = AnalysisAgent(document_store=document_store)
    agent_input = AgentInput(
        task_id=uuid.uuid4(), case_id=None, context={"document_id": document.document_id}
    )

    output = await agent.run(agent_input)

    entities = output.result["entities"]
    assert [e["value"] for e in entities["persons"]] == ["Jean Dupont"]
    assert [e["value"] for e in entities["companies"]] == ["Acme SARL"]
    assert [e["value"] for e in entities["dates"]] == ["2024-03-12"]
    assert [e["value"] for e in entities["amounts"]] == ["1200 EUR"]
    assert output.result["narrative"]
    assert output.citations[0].source_id == document.document_id
    assert output.confidence in (ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH)


@pytest.mark.asyncio
async def test_analysis_agent_surfaces_case_timeline_inconsistencies() -> None:
    document_store = InMemoryDocumentStore()
    document = _make_document()
    document_store.save(document)

    case_store = InMemoryCaseStore()
    case_id = str(uuid.uuid4())
    case_profile = CaseProfile(
        case_id=case_id,
        title="Dupont c/ Acme",
        timeline=[
            CaseTimelineEntry(
                date="2024-03-12",
                description="Signature du bail",
                document_ids=("doc-1",),
                confidence=0.9,
            )
        ],
        timeline_inconsistencies=[
            TimelineInconsistency(
                date="2024-03-12",
                entries=(
                    CaseTimelineEntry(
                        date="2024-03-12",
                        description="Signature du bail",
                        document_ids=("doc-1",),
                        confidence=0.9,
                    ),
                    CaseTimelineEntry(
                        date="2024-03-12",
                        description="Resiliation anticipee",
                        document_ids=("doc-2",),
                        confidence=0.6,
                    ),
                ),
            )
        ],
    )
    case_store.save(case_profile)

    agent = AnalysisAgent(document_store=document_store, case_store=case_store)
    agent_input = AgentInput(
        task_id=uuid.uuid4(),
        case_id=uuid.UUID(case_id),
        context={"document_id": document.document_id},
    )

    output = await agent.run(agent_input)

    assert len(output.result["inconsistencies"]) == 1
    assert output.result["inconsistencies"][0]["date"] == "2024-03-12"
    assert len(output.result["timeline"]) == 1


@pytest.mark.asyncio
async def test_analysis_agent_low_confidence_when_document_has_no_entities() -> None:
    document_store = InMemoryDocumentStore()
    document = DocumentRecord(
        document_id="doc-empty",
        filename="scan-vierge.pdf",
        status=ProcessingStatus.RECEIVED,
        raw_bytes=b"%PDF-1.4 fake",
        ocr_text="",
    )
    document_store.save(document)

    agent = AnalysisAgent(document_store=document_store)
    agent_input = AgentInput(
        task_id=uuid.uuid4(), case_id=None, context={"document_id": document.document_id}
    )

    output = await agent.run(agent_input)

    assert output.confidence == ConfidenceLevel.LOW
    assert any("no pre-extracted entities" in warning for warning in output.warnings)


@pytest.mark.asyncio
async def test_analysis_agent_warns_when_case_id_not_found() -> None:
    document_store = InMemoryDocumentStore()
    document = _make_document()
    document_store.save(document)

    agent = AnalysisAgent(document_store=document_store, case_store=InMemoryCaseStore())
    missing_case_id = uuid.uuid4()
    agent_input = AgentInput(
        task_id=uuid.uuid4(),
        case_id=missing_case_id,
        context={"document_id": document.document_id},
    )

    output = await agent.run(agent_input)

    assert any(str(missing_case_id) in warning for warning in output.warnings)


@pytest.mark.asyncio
async def test_analysis_agent_routes_model_through_fabric() -> None:
    document_store = InMemoryDocumentStore()
    document = _make_document()
    document_store.save(document)

    agent = AnalysisAgent(
        document_store=document_store, fabric=get_ai_intelligence_fabric(), firm_id="firm-test"
    )
    agent_input = AgentInput(
        task_id=uuid.uuid4(), case_id=None, context={"document_id": document.document_id}
    )

    output = await agent.run(agent_input)

    assert output.result["model"] != "default"


@pytest.mark.asyncio
async def test_analysis_agent_records_explainability_with_case_profile() -> None:
    document_store = InMemoryDocumentStore()
    document = _make_document()
    document_store.save(document)

    case_store = InMemoryCaseStore()
    case_id = str(uuid.uuid4())
    case_store.save(CaseProfile(case_id=case_id, title="Dupont c/ Acme"))

    governance = get_ai_governance_platform()
    agent = AnalysisAgent(
        document_store=document_store,
        case_store=case_store,
        governance=governance,
        firm_id="firm-explainability-test",
    )
    task_id = uuid.uuid4()
    agent_input = AgentInput(
        task_id=task_id,
        case_id=uuid.UUID(case_id),
        context={"document_id": document.document_id},
    )

    await agent.run(agent_input)

    report = governance.explainability.latest("firm-explainability-test", str(task_id))
    assert report is not None
    assert any("dossier" in step for step in report.steps_followed)
