"""End-to-end: a Synthesis output carrying a real conflict, an
uncited (hallucination-risk) narrative and a biased sentence — all
produced by the real `SynthesisAgent`, never mocked or hand-crafted —
is flagged only because Sprint 31 makes the fused output pass through
`VerifierAgent.verify()` a second time, after "synthesis", instead of
reaching `END` unchecked (the Sprint 30 graph bug this sprint fixes;
see docs/159-architecture-agent-verificateur.md)."""

import uuid

import pytest

from tmis.agents.analysis_agent import AnalysisAgent
from tmis.agents.contracts import AgentInput, ConfidenceLevel
from tmis.agents.orchestrator import Orchestrator
from tmis.agents.synthesis_agent import SynthesisAgent
from tmis.agents.verifier_agent import VerifierAgent
from tmis.ai.kernel.kernel import TMISKernel
from tmis.case_intelligence.actors.schemas import Actor, ActorType, CaseActorRole
from tmis.case_intelligence.cases.in_memory_store import InMemoryCaseStore
from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.case_intelligence.facts.schemas import Fact
from tmis.case_intelligence.issues.schemas import IssueStatus, LegalIssue
from tmis.case_intelligence.timeline.schemas import CaseTimelineEntry
from tmis.document_intelligence.schemas.document import ProcessingStatus
from tmis.document_intelligence.schemas.entities import EntityType, ExtractedEntity
from tmis.document_intelligence.schemas.record import DocumentRecord
from tmis.document_intelligence.storage.in_memory_store import InMemoryDocumentStore

_BIASED_OPEN_ISSUE = (
    "Les femmes sont désavantagées par la clause de non-concurrence de ce contrat."
)


def _build_case() -> CaseProfile:
    actor = Actor(id="actor-1", type=ActorType.PERSON, name="Marie Curie")
    return CaseProfile(
        case_id=str(uuid.uuid4()),
        title="Curie c/ Techcorp",
        actors=[actor],
        actor_roles={"actor-1": CaseActorRole.CLIENT},
        document_ids={"doc-1"},
        timeline=[
            CaseTimelineEntry(
                date="2024-05-01",
                description="Assignation deposee",
                document_ids=("doc-1",),
                confidence=0.9,
            )
        ],
        facts=[
            Fact(
                id="fact-1",
                description="Rupture du contrat",
                confidence=0.85,
                source_document_ids={"doc-1"},
                # A contradicting document is what makes
                # `HeuristicConflictDetector` report a real conflict —
                # nothing about this is invented by the Verifier.
                contradicting_document_ids={"doc-2"},
            )
        ],
        legal_issues=[
            LegalIssue(id="issue-1", description=_BIASED_OPEN_ISSUE, status=IssueStatus.OPEN)
        ],
    )


def _build_document() -> DocumentRecord:
    return DocumentRecord(
        document_id="doc-1",
        filename="assignation.pdf",
        status=ProcessingStatus.ENTITIES_EXTRACTED,
        raw_bytes=b"%PDF-1.4 fake",
        # Contains a citation marker (`article 1234`) on purpose: this
        # keeps AnalysisAgent's own narrative hallucination-free, so the
        # test isolates what Sprint 31 actually fixes — Synthesis's
        # output reaching the Verifier — rather than conflating it with
        # Analysis's own (already-verified pre-Sprint-31) narrative.
        ocr_text="Assignation devant le Tribunal judiciaire, voir article 1234 du code civil.",
        entities=[ExtractedEntity(type=EntityType.PERSON, value="Marie Curie", confidence=0.92)],
    )


@pytest.mark.asyncio
async def test_synthesis_conflict_hallucination_bias_flagged_after_full_graph() -> None:
    case_store = InMemoryCaseStore()
    case_profile = _build_case()
    case_store.save(case_profile)

    document_store = InMemoryDocumentStore()
    document_store.save(_build_document())

    kernel = TMISKernel()

    synthesis_agent = SynthesisAgent(kernel=kernel, case_store=case_store)

    # Proof that this is genuinely invisible without the Verifier: run
    # `SynthesisAgent` on its own first, exactly the call the pre-Sprint-31
    # graph made and then routed straight past the Verifier.
    agent_input = AgentInput(
        task_id=uuid.uuid4(),
        case_id=case_profile.case_id,
        context={"document_id": "doc-1"},
    )
    raw_synthesis_output = await synthesis_agent.run(agent_input)
    assert raw_synthesis_output.confidence == ConfidenceLevel.HIGH
    assert raw_synthesis_output.warnings == []

    orchestrator = Orchestrator(
        analysis_agent=AnalysisAgent(
            kernel=kernel, document_store=document_store, case_store=case_store
        ),
        verifier_agent=VerifierAgent(case_store=case_store),
        synthesis_agent=SynthesisAgent(kernel=kernel, case_store=case_store),
    )

    output = await orchestrator.run(agent_input)

    # Nothing Analysis or Synthesis produced was deleted or rewritten —
    # only warnings were added and confidence was adjusted.
    assert output.result["entities"]["persons"][0]["value"] == "Marie Curie"
    synthesis_result = output.result["synthesis"]
    assert synthesis_result["synthesis_note"]
    assert synthesis_result["executive_summary"]
    assert synthesis_result["table"]["actors"][0]["name"] == "Marie Curie"

    assert any("Conflict detected" in warning for warning in output.warnings)
    assert any("fact_inconsistency" in warning for warning in output.warnings)
    assert any("Hallucination risk" in warning for warning in output.warnings)
    assert any("Bias detected" in warning for warning in output.warnings)

    # Three signal categories (conflict, hallucination, bias) fired in the
    # final `verifier_final` pass on a HIGH-confidence fused output:
    # HIGH -> MEDIUM -> LOW in that single call.
    assert output.confidence == ConfidenceLevel.LOW
