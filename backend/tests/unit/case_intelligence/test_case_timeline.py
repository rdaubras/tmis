from tmis.case_intelligence.timeline.engine import CaseTimelineEngine
from tmis.document_intelligence.schemas.timeline import TimelineEvent


def _event(date: str, description: str, document_id: str, confidence: float = 0.6) -> TimelineEvent:
    return TimelineEvent(
        date=date, description=description, document_id=document_id, confidence=confidence
    )


def test_consolidate_creates_new_entries() -> None:
    engine = CaseTimelineEngine()
    entries = engine.consolidate([], [_event("12 janvier 2019", "Signature", "doc-1")])
    assert len(entries) == 1
    assert entries[0].document_ids == ("doc-1",)


def test_consolidate_merges_identical_entry_from_another_document() -> None:
    engine = CaseTimelineEngine()
    entries = engine.consolidate([], [_event("12 janvier 2019", "Signature", "doc-1")])
    entries = engine.consolidate(entries, [_event("12 janvier 2019", "Signature", "doc-2")])

    assert len(entries) == 1
    assert entries[0].document_ids == ("doc-1", "doc-2")
    assert entries[0].confidence > 0.6


def test_consolidate_sorts_chronologically() -> None:
    engine = CaseTimelineEngine()
    entries = engine.consolidate(
        [],
        [
            _event("03/06/2021", "Mise en demeure", "doc-2"),
            _event("12 janvier 2019", "Signature", "doc-1"),
        ],
    )
    assert [e.date for e in entries] == ["12 janvier 2019", "03/06/2021"]


def test_detect_inconsistencies_flags_same_date_different_description() -> None:
    engine = CaseTimelineEngine()
    entries = engine.consolidate([], [_event("12 janvier 2019", "Signature", "doc-1")])
    entries = engine.consolidate(entries, [_event("12 janvier 2019", "Résiliation", "doc-2")])

    inconsistencies = engine.detect_inconsistencies(entries)

    assert len(inconsistencies) == 1
    assert inconsistencies[0].date == "12 janvier 2019"
    assert len(inconsistencies[0].entries) == 2


def test_detect_inconsistencies_returns_empty_for_clean_timeline() -> None:
    engine = CaseTimelineEngine()
    entries = engine.consolidate([], [_event("12 janvier 2019", "Signature", "doc-1")])
    assert engine.detect_inconsistencies(entries) == []


def test_consolidate_does_not_duplicate_same_document_twice() -> None:
    engine = CaseTimelineEngine()
    event = _event("12 janvier 2019", "Signature", "doc-1")
    entries = engine.consolidate([], [event])
    entries = engine.consolidate(entries, [event])
    assert len(entries) == 1
    assert entries[0].document_ids == ("doc-1",)
