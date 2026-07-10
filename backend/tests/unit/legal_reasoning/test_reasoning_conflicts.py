from tmis.case_intelligence.facts.schemas import Fact
from tmis.case_intelligence.timeline.schemas import CaseTimelineEntry, TimelineInconsistency
from tmis.legal_reasoning.conflicts.engine import HeuristicConflictDetector
from tmis.legal_reasoning.conflicts.schemas import ConflictType


def test_detect_flags_fact_inconsistency() -> None:
    fact = Fact(
        id="f1",
        description="fact",
        confidence=0.8,
        source_document_ids={"d1"},
        contradicting_document_ids={"d2"},
    )
    conflicts = HeuristicConflictDetector().detect([fact], [])
    types = {c.type for c in conflicts}
    assert ConflictType.FACT_INCONSISTENCY in types


def test_detect_flags_document_contradiction_pair() -> None:
    fact = Fact(
        id="f1",
        description="fact",
        confidence=0.8,
        source_document_ids={"d1"},
        contradicting_document_ids={"d2"},
    )
    conflicts = HeuristicConflictDetector().detect([fact], [])
    doc_conflicts = [c for c in conflicts if c.type == ConflictType.DOCUMENT_CONTRADICTION]
    assert len(doc_conflicts) == 1
    assert set(doc_conflicts[0].involved_ids) == {"d1", "d2"}


def test_detect_flags_temporal_contradiction() -> None:
    entry_a = CaseTimelineEntry(
        date="2020-01-01", description="A", document_ids=("d1",), confidence=0.5
    )
    entry_b = CaseTimelineEntry(
        date="2020-01-01", description="B", document_ids=("d2",), confidence=0.5
    )
    inconsistency = TimelineInconsistency(date="2020-01-01", entries=(entry_a, entry_b))

    conflicts = HeuristicConflictDetector().detect([], [inconsistency])

    assert len(conflicts) == 1
    assert conflicts[0].type == ConflictType.TEMPORAL_CONTRADICTION
    assert set(conflicts[0].involved_ids) == {"d1", "d2"}


def test_detect_flags_duplicate_facts() -> None:
    fact_a = Fact(id="f1", description="Le contrat a été signé.", confidence=0.5)
    fact_b = Fact(id="f2", description="le contrat a été signé.", confidence=0.5)

    conflicts = HeuristicConflictDetector().detect([fact_a, fact_b], [])

    duplicates = [c for c in conflicts if c.type == ConflictType.DUPLICATE]
    assert len(duplicates) == 1
    assert set(duplicates[0].involved_ids) == {"f1", "f2"}


def test_detect_returns_nothing_for_clean_facts() -> None:
    fact = Fact(id="f1", description="fact non contesté", confidence=0.9)
    assert HeuristicConflictDetector().detect([fact], []) == []
