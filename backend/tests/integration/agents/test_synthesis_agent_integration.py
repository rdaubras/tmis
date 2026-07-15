"""End-to-end: a case persisted through `CaseStorePort` (Sprint 26) is
synthesized by the real `SynthesisAgent` (Sprint 30) via the `Orchestrator`,
producing case-level deliverables (executive summary reused from
`CaseSummaryGenerator`, structured table, fact sheet, checklist, and a
narrative synthesis note generated through `TMISKernel.complete()`) fused
into the analysis/verifier output — plus a governance explainability
report."""

import uuid

import pytest

from tmis.agents.analysis_agent import AnalysisAgent
from tmis.agents.contracts import AgentInput, ConfidenceLevel
from tmis.agents.orchestrator import Orchestrator
from tmis.agents.synthesis_agent import SynthesisAgent
from tmis.ai.kernel.kernel import TMISKernel
from tmis.ai_governance.bootstrap import get_ai_governance_platform
from tmis.case_intelligence.actors.schemas import Actor, ActorType, CaseActorRole
from tmis.case_intelligence.cases.in_memory_store import InMemoryCaseStore
from tmis.case_intelligence.cases.schemas import CaseProfile, CaseTask
from tmis.case_intelligence.facts.schemas import Fact
from tmis.case_intelligence.issues.schemas import LegalIssue
from tmis.case_intelligence.timeline.schemas import CaseTimelineEntry
from tmis.document_intelligence.schemas.document import ProcessingStatus
from tmis.document_intelligence.schemas.entities import EntityType, ExtractedEntity
from tmis.document_intelligence.schemas.record import DocumentRecord
from tmis.document_intelligence.storage.in_memory_store import InMemoryDocumentStore


@pytest.mark.asyncio
async def test_persisted_case_flows_through_synthesis_agent_via_orchestrator() -> None:
    case_store = InMemoryCaseStore()
    case_id = str(uuid.uuid4())
    actor = Actor(id="actor-1", type=ActorType.PERSON, name="Marie Curie")
    case_profile = CaseProfile(
        case_id=case_id,
        title="Curie c/ Techcorp",
        actors=[actor],
        actor_roles={"actor-1": CaseActorRole.CLIENT},
        document_ids={"doc-1"},
        timeline=[
            CaseTimelineEntry(
                date="2024-05-01",
                description="Assignation delivree",
                document_ids=("doc-1",),
                confidence=0.9,
            )
        ],
        facts=[Fact(id="fact-1", description="Rupture du contrat", confidence=0.85)],
        legal_issues=[LegalIssue(id="issue-1", description="Qualification de la rupture")],
        tasks=[CaseTask(id="task-1", description="Preparer les conclusions", done=False)],
    )
    case_store.save(case_profile)

    document_store = InMemoryDocumentStore()
    document = DocumentRecord(
        document_id="doc-1",
        filename="assignation.pdf",
        status=ProcessingStatus.ENTITIES_EXTRACTED,
        raw_bytes=b"%PDF-1.4 fake",
        ocr_text="Assignation devant le Tribunal judiciaire, Marie Curie contre Techcorp SA.",
        entities=[
            ExtractedEntity(type=EntityType.PERSON, value="Marie Curie", confidence=0.92),
        ],
    )
    document_store.save(document)

    kernel = TMISKernel()
    governance = get_ai_governance_platform()

    analysis_agent = AnalysisAgent(
        kernel=kernel, document_store=document_store, governance=governance, firm_id="firm-test"
    )
    synthesis_agent = SynthesisAgent(
        kernel=kernel, case_store=case_store, governance=governance, firm_id="firm-test"
    )
    orchestrator = Orchestrator(analysis_agent=analysis_agent, synthesis_agent=synthesis_agent)

    task_id = uuid.uuid4()
    agent_input = AgentInput(
        task_id=task_id,
        case_id=case_id,
        context={"document_id": document.document_id},
    )

    output = await orchestrator.run(agent_input)

    # The analysis result stays intact — Synthesis is fused in, not swapped in.
    assert output.result["entities"]["persons"][0]["value"] == "Marie Curie"

    synthesis_result = output.result["synthesis"]
    assert synthesis_result["executive_summary"]
    assert synthesis_result["table"]["actors"][0]["name"] == "Marie Curie"
    assert synthesis_result["table"]["deadlines"][0]["description"] == "Preparer les conclusions"
    assert synthesis_result["fact_sheet"]["title"] == "Curie c/ Techcorp"
    assert any(
        entry["item"] == "Qualification de la rupture" for entry in synthesis_result["checklist"]
    )
    assert synthesis_result["synthesis_note"]

    assert output.confidence in (ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH)
    assert any(citation.source_id == case_id for citation in output.citations)

    # Both agents recorded explainability under the same production id
    # (this task): analysis first, then synthesis — `history()` keeps both.
    history = governance.explainability.history("firm-test", str(task_id))
    agents_involved = {agent for report in history for agent in report.agents_involved}
    assert agents_involved == {"analysis", "synthesis"}
