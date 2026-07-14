"""End-to-end: a document persisted through `DocumentStorePort` (Sprint 26)
is analyzed by the real `AnalysisAgent` (Sprint 29) via the `Orchestrator`,
producing a result usable downstream (structured entities, a narrative
generated through `TMISKernel.complete()`, and a governance explainability
report)."""

import uuid

import pytest

from tmis.agents.analysis_agent import AnalysisAgent
from tmis.agents.contracts import AgentInput, ConfidenceLevel
from tmis.agents.orchestrator import Orchestrator
from tmis.ai.kernel.kernel import TMISKernel
from tmis.ai_governance.bootstrap import get_ai_governance_platform
from tmis.document_intelligence.schemas.document import ProcessingStatus
from tmis.document_intelligence.schemas.entities import EntityType, ExtractedEntity
from tmis.document_intelligence.schemas.record import DocumentRecord
from tmis.document_intelligence.storage.in_memory_store import InMemoryDocumentStore


@pytest.mark.asyncio
async def test_persisted_document_flows_through_analysis_agent_and_verifier() -> None:
    document_store = InMemoryDocumentStore()
    document = DocumentRecord(
        document_id=str(uuid.uuid4()),
        filename="assignation.pdf",
        status=ProcessingStatus.ENTITIES_EXTRACTED,
        raw_bytes=b"%PDF-1.4 fake",
        ocr_text=(
            "Assignation devant le Tribunal judiciaire de Paris, "
            "Marie Curie contre Techcorp SA, montant reclame 50000 EUR."
        ),
        entities=[
            ExtractedEntity(type=EntityType.PERSON, value="Marie Curie", confidence=0.92),
            ExtractedEntity(type=EntityType.COMPANY, value="Techcorp SA", confidence=0.88),
            ExtractedEntity(
                type=EntityType.JURISDICTION,
                value="Tribunal judiciaire de Paris",
                confidence=0.9,
            ),
            ExtractedEntity(type=EntityType.AMOUNT, value="50000 EUR", confidence=0.8),
        ],
    )
    document_store.save(document)

    kernel = TMISKernel()
    governance = get_ai_governance_platform()

    analysis_agent = AnalysisAgent(
        kernel=kernel,
        document_store=document_store,
        governance=governance,
        firm_id="firm-test",
    )
    orchestrator = Orchestrator(analysis_agent=analysis_agent)

    task_id = uuid.uuid4()
    agent_input = AgentInput(
        task_id=task_id, case_id=None, context={"document_id": document.document_id}
    )

    output = await orchestrator.run(agent_input)

    assert output.confidence in (ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH)
    entities = output.result["entities"]
    assert [e["value"] for e in entities["persons"]] == ["Marie Curie"]
    assert [e["value"] for e in entities["companies"]] == ["Techcorp SA"]
    assert [e["value"] for e in entities["jurisdictions"]] == ["Tribunal judiciaire de Paris"]
    assert output.result["narrative"]
    assert output.citations[0].reference == "assignation.pdf"

    report = governance.explainability.latest("firm-test", str(task_id))
    assert report is not None
    assert document.document_id in report.documents_consulted
