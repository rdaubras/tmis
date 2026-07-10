from tmis.case_intelligence.facts.engine import FactEngine
from tmis.case_intelligence.facts.schemas import Fact
from tmis.document_intelligence.schemas.timeline import TimelineEvent


def _event(date: str, description: str, document_id: str, confidence: float = 0.6) -> TimelineEvent:
    return TimelineEvent(
        date=date, description=description, document_id=document_id, confidence=confidence
    )


def test_ingest_creates_a_new_fact() -> None:
    engine = FactEngine()
    facts = engine.ingest([], [_event("12 janvier 2019", "Signature", "doc-1")], "doc-1")
    assert len(facts) == 1
    assert facts[0].source_document_ids == {"doc-1"}


def test_ingest_corroborates_an_identical_fact_from_another_document() -> None:
    engine = FactEngine()
    facts = engine.ingest([], [_event("12 janvier 2019", "Signature", "doc-1")], "doc-1")
    facts = engine.ingest(facts, [_event("12 janvier 2019", "Signature", "doc-2")], "doc-2")

    assert len(facts) == 1
    assert facts[0].confirming_document_ids == {"doc-2"}
    assert facts[0].confidence > 0.6


def test_ingest_flags_contradiction_for_same_date_different_description() -> None:
    engine = FactEngine()
    facts = engine.ingest([], [_event("12 janvier 2019", "Signature", "doc-1")], "doc-1")
    facts = engine.ingest(facts, [_event("12 janvier 2019", "Résiliation", "doc-2")], "doc-2")

    assert len(facts) == 2
    signature = next(f for f in facts if f.description == "Signature")
    resiliation = next(f for f in facts if f.description == "Résiliation")
    assert signature.contradicting_document_ids == {"doc-2"}
    assert resiliation.contradicting_document_ids == {"doc-1"}


def test_ingest_does_not_duplicate_same_document_confirming_twice() -> None:
    engine = FactEngine()
    event = _event("12 janvier 2019", "Signature", "doc-1")
    facts = engine.ingest([], [event], "doc-1")
    facts = engine.ingest(facts, [event], "doc-1")
    assert len(facts) == 1
    assert facts[0].confirming_document_ids == set()


def test_confidence_never_exceeds_one() -> None:
    engine = FactEngine(confirmation_boost=0.5)
    facts: list[Fact] = []
    for i in range(5):
        event = _event("12 janvier 2019", "Signature", f"doc-{i}", confidence=0.9)
        facts = engine.ingest(facts, [event], f"doc-{i}")
    assert facts[0].confidence <= 1.0
