from tmis.case_intelligence.evidence.linker import EvidenceLinker
from tmis.case_intelligence.evidence.schemas import EvidenceConfidence
from tmis.case_intelligence.facts.schemas import Fact


def _fact(confidence: float, *, confirming: set[str] | None = None) -> Fact:
    return Fact(
        id="f1",
        description="Signature",
        confidence=confidence,
        source_document_ids={"doc-1"},
        confirming_document_ids=confirming or set(),
    )


def test_high_confidence_source_document_is_direct_evidence() -> None:
    links = EvidenceLinker().link(_fact(0.9))
    assert links[0].confidence == EvidenceConfidence.DIRECT
    assert links[0].document_id == "doc-1"


def test_mid_confidence_source_document_is_circumstantial() -> None:
    links = EvidenceLinker().link(_fact(0.6))
    assert links[0].confidence == EvidenceConfidence.CIRCUMSTANTIAL


def test_low_confidence_fact_is_always_weak_evidence() -> None:
    links = EvidenceLinker().link(_fact(0.2, confirming={"doc-2"}))
    assert all(link.confidence == EvidenceConfidence.WEAK for link in links)


def test_confirming_documents_are_corroborating_evidence() -> None:
    links = EvidenceLinker().link(_fact(0.9, confirming={"doc-2"}))
    corroborating = next(link for link in links if link.document_id == "doc-2")
    assert corroborating.confidence == EvidenceConfidence.CORROBORATING


def test_link_count_matches_source_plus_confirming_documents() -> None:
    links = EvidenceLinker().link(_fact(0.9, confirming={"doc-2", "doc-3"}))
    assert len(links) == 3
    assert all(link.fact_id == "f1" for link in links)
