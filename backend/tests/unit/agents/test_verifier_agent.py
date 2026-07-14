import pytest

from tmis.agents.contracts import AgentOutput, ConfidenceLevel
from tmis.agents.verifier_agent import VerifierAgent
from tmis.ai.schemas.citation import Citation
from tmis.case_intelligence.cases.in_memory_store import InMemoryCaseStore
from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.case_intelligence.facts.schemas import Fact
from tmis.case_intelligence.timeline.schemas import CaseTimelineEntry, TimelineInconsistency

_CASE_ID = "case-1"


def _case_citation(case_id: str = _CASE_ID) -> Citation:
    return Citation(source_id=case_id, connector="case_store", excerpt="Résumé.", reference="Titre")


@pytest.mark.asyncio
async def test_verifier_detects_case_conflicts_via_case_store() -> None:
    case_store = InMemoryCaseStore()
    case_store.save(
        CaseProfile(
            case_id=_CASE_ID,
            title="Dossier",
            facts=[
                Fact(
                    id="fact-1",
                    description="Rupture du contrat",
                    confidence=0.8,
                    source_document_ids={"doc-1"},
                    contradicting_document_ids={"doc-2"},
                )
            ],
        )
    )
    verifier = VerifierAgent(case_store=case_store)
    output = AgentOutput(
        result={}, citations=[_case_citation()], confidence=ConfidenceLevel.HIGH
    )

    verified = await verifier.verify(output)

    assert any("Conflict detected" in warning for warning in verified.warnings)
    assert verified.confidence == ConfidenceLevel.MEDIUM


@pytest.mark.asyncio
async def test_verifier_skips_case_coherence_without_case_store_citation() -> None:
    verifier = VerifierAgent(case_store=InMemoryCaseStore())
    output = AgentOutput(
        result={},
        citations=[
            Citation(source_id="doc-1", connector="document_store", excerpt="x", reference="y")
        ],
        confidence=ConfidenceLevel.HIGH,
    )

    verified = await verifier.verify(output)

    assert verified.warnings == []
    assert verified.confidence == ConfidenceLevel.HIGH


@pytest.mark.asyncio
async def test_verifier_skips_case_coherence_when_case_not_found() -> None:
    verifier = VerifierAgent(case_store=InMemoryCaseStore())
    output = AgentOutput(
        result={}, citations=[_case_citation("missing")], confidence=ConfidenceLevel.HIGH
    )

    verified = await verifier.verify(output)

    assert verified.warnings == []
    assert verified.confidence == ConfidenceLevel.HIGH


@pytest.mark.asyncio
async def test_verifier_reuses_conflict_detector_output_unchanged() -> None:
    """Composition, not reimplementation: the conflicts the Verifier
    reports must be exactly what `HeuristicConflictDetector.detect()`
    already computed from `facts`/`timeline_inconsistencies`."""
    case_store = InMemoryCaseStore()
    entry = CaseTimelineEntry(
        date="2024-05-01", description="A", document_ids=("doc-1",), confidence=0.9
    )
    other_entry = CaseTimelineEntry(
        date="2024-05-01", description="B", document_ids=("doc-2",), confidence=0.9
    )
    inconsistency = TimelineInconsistency(date="2024-05-01", entries=(entry, other_entry))
    case_store.save(
        CaseProfile(
            case_id=_CASE_ID, title="Dossier", timeline_inconsistencies=[inconsistency]
        )
    )

    verifier = VerifierAgent(case_store=case_store)
    output = AgentOutput(result={}, citations=[_case_citation()], confidence=ConfidenceLevel.MEDIUM)

    verified = await verifier.verify(output)

    assert any("temporal_contradiction" in warning for warning in verified.warnings)
    assert any(inconsistency.reason in warning for warning in verified.warnings)


@pytest.mark.asyncio
async def test_verifier_detects_hallucination_risk_in_narrative() -> None:
    verifier = VerifierAgent(case_store=InMemoryCaseStore())
    output = AgentOutput(
        result={"narrative": "Le client a signé le contrat le mois dernier sans réserve."},
        confidence=ConfidenceLevel.HIGH,
    )

    verified = await verifier.verify(output)

    assert any("Hallucination risk" in warning for warning in verified.warnings)
    assert verified.confidence == ConfidenceLevel.MEDIUM


@pytest.mark.asyncio
async def test_verifier_detects_bias_in_synthesis_note() -> None:
    verifier = VerifierAgent(case_store=InMemoryCaseStore())
    # Carries a citation marker (`article 5`) on purpose so only the bias
    # check fires here — the hallucination cascade is covered by its own
    # dedicated test above.
    output = AgentOutput(
        result={
            "synthesis_note": (
                "Les femmes sont moins susceptibles d'agir en justice, "
                "voir article 5 du code civil."
            )
        },
        confidence=ConfidenceLevel.HIGH,
    )

    verified = await verifier.verify(output)

    assert any("Bias detected" in warning for warning in verified.warnings)
    assert not any("Hallucination risk" in warning for warning in verified.warnings)
    assert verified.confidence == ConfidenceLevel.MEDIUM


@pytest.mark.asyncio
async def test_verifier_extracts_narrative_from_nested_synthesis_key() -> None:
    """After `_fuse_with_synthesis`, Synthesis's own result lives under a
    top-level `"synthesis"` key rather than inline — the extraction must
    still reach it without the Orchestrator renaming anything."""
    verifier = VerifierAgent(case_store=InMemoryCaseStore())
    output = AgentOutput(
        result={
            "narrative": "",
            "synthesis": {
                "synthesis_note": "Un texte de synthèse sans aucune source citée ici."
            },
        },
        confidence=ConfidenceLevel.HIGH,
    )

    verified = await verifier.verify(output)

    assert any("Hallucination risk" in warning for warning in verified.warnings)


@pytest.mark.asyncio
async def test_verifier_confidence_cascades_to_low_with_multiple_signal_categories() -> None:
    case_store = InMemoryCaseStore()
    case_store.save(
        CaseProfile(
            case_id=_CASE_ID,
            title="Dossier",
            facts=[
                Fact(
                    id="fact-1",
                    description="Rupture du contrat",
                    confidence=0.8,
                    source_document_ids={"doc-1"},
                    contradicting_document_ids={"doc-2"},
                )
            ],
        )
    )
    verifier = VerifierAgent(case_store=case_store)
    output = AgentOutput(
        result={"narrative": "Les femmes sont moins présentes dans ce contentieux."},
        citations=[_case_citation()],
        confidence=ConfidenceLevel.HIGH,
    )

    verified = await verifier.verify(output)

    # Three categories fire at once: conflict, hallucination (no citation
    # marker) and bias — HIGH -> MEDIUM -> LOW in the same call.
    assert verified.confidence == ConfidenceLevel.LOW
    assert any("Conflict detected" in warning for warning in verified.warnings)
    assert any("Hallucination risk" in warning for warning in verified.warnings)
    assert any("Bias detected" in warning for warning in verified.warnings)


@pytest.mark.asyncio
async def test_verifier_never_removes_or_rewrites_content() -> None:
    verifier = VerifierAgent(case_store=InMemoryCaseStore())
    result = {"narrative": "Texte sans citation.", "entities": {"persons": []}}
    citations = [
        Citation(source_id="doc-1", connector="document_store", excerpt="x", reference="y")
    ]
    output = AgentOutput(result=result, citations=citations, confidence=ConfidenceLevel.HIGH)

    verified = await verifier.verify(output)

    assert verified.result == result
    assert verified.citations == citations
    assert len(verified.warnings) >= 1
