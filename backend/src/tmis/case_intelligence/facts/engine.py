import re
import uuid

from tmis.case_intelligence.facts.schemas import Fact
from tmis.document_intelligence.schemas.timeline import TimelineEvent

_WHITESPACE_RE = re.compile(r"\s+")


def _normalize(description: str) -> str:
    return _WHITESPACE_RE.sub(" ", description.strip().lower())


class FactEngine:
    """Implements `FactEnginePort`: turns per-document timeline events into
    case-level facts, corroborating a fact already on record instead of
    duplicating it, and cross-referencing facts that disagree about the
    same date (see docs/19-case-intelligence.md).
    """

    def __init__(self, *, confirmation_boost: float = 0.1) -> None:
        self._confirmation_boost = confirmation_boost

    def ingest(
        self, facts: list[Fact], events: list[TimelineEvent], document_id: str
    ) -> list[Fact]:
        updated = list(facts)

        for event in events:
            normalized = _normalize(event.description)
            match = next(
                (fact for fact in updated if _normalize(fact.description) == normalized), None
            )
            if match is not None:
                already_known = (
                    document_id in match.source_document_ids
                    or document_id in match.confirming_document_ids
                )
                if not already_known:
                    match.confirming_document_ids.add(document_id)
                    match.confidence = min(1.0, match.confidence + self._confirmation_boost)
                continue

            same_date_facts = [fact for fact in updated if event.date in fact.dates]
            new_fact = Fact(
                id=str(uuid.uuid4()),
                description=event.description,
                confidence=event.confidence,
                dates=(event.date,),
                source_document_ids={document_id},
            )
            for other in same_date_facts:
                other.contradicting_document_ids.add(document_id)
                new_fact.contradicting_document_ids |= other.source_document_ids
            updated.append(new_fact)

        return updated
