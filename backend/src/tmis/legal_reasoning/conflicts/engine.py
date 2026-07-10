import uuid
from collections import defaultdict

from tmis.case_intelligence.facts.schemas import Fact
from tmis.case_intelligence.timeline.schemas import TimelineInconsistency
from tmis.legal_reasoning.conflicts.schemas import Conflict, ConflictType


class HeuristicConflictDetector:
    """Implements `ConflictDetectorPort`, reusing what the Case
    Intelligence Engine (Sprint 4) already computed rather than
    re-detecting contradictions from scratch (see
    docs/25-legal-reasoning.md — Conflict Detector):

    - **fact_inconsistency**: one conflict per fact that already carries
      `contradicting_document_ids` (`FactEngine`, Sprint 4).
    - **document_contradiction**: one conflict per (source document,
      contradicting document) pair drawn from that same data — the
      document-level view of the same underlying disagreement.
    - **temporal_contradiction**: one conflict per `TimelineInconsistency`
      (`CaseTimelineEngine`, Sprint 4).
    - **duplicate**: new to this sprint — facts sharing the exact same
      normalized description under different ids.
    """

    def detect(
        self, facts: list[Fact], timeline_inconsistencies: list[TimelineInconsistency]
    ) -> list[Conflict]:
        conflicts: list[Conflict] = []
        conflicts.extend(self._fact_inconsistencies(facts))
        conflicts.extend(self._document_contradictions(facts))
        conflicts.extend(self._temporal_contradictions(timeline_inconsistencies))
        conflicts.extend(self._duplicates(facts))
        return conflicts

    def _fact_inconsistencies(self, facts: list[Fact]) -> list[Conflict]:
        return [
            Conflict(
                id=str(uuid.uuid4()),
                type=ConflictType.FACT_INCONSISTENCY,
                description=f"Le fait « {fact.description} » est contesté par le dossier.",
                explanation=(
                    f"{len(fact.contradicting_document_ids)} document(s) contredisent ce fait, "
                    f"contre {len(fact.confirming_document_ids)} qui le confirment."
                ),
                involved_ids=(fact.id,),
            )
            for fact in facts
            if fact.contradicting_document_ids
        ]

    def _document_contradictions(self, facts: list[Fact]) -> list[Conflict]:
        conflicts = []
        for fact in facts:
            if not fact.contradicting_document_ids:
                continue
            for source_doc in fact.source_document_ids or {"?"}:
                for contra_doc in fact.contradicting_document_ids:
                    conflicts.append(
                        Conflict(
                            id=str(uuid.uuid4()),
                            type=ConflictType.DOCUMENT_CONTRADICTION,
                            description=(
                                f"Le document {source_doc!r} et le document {contra_doc!r} "
                                "se contredisent."
                            ),
                            explanation=(
                                f"Portent tous deux sur le fait « {fact.description} » "
                                "avec des versions incompatibles."
                            ),
                            involved_ids=(source_doc, contra_doc),
                        )
                    )
        return conflicts

    def _temporal_contradictions(
        self, timeline_inconsistencies: list[TimelineInconsistency]
    ) -> list[Conflict]:
        return [
            Conflict(
                id=str(uuid.uuid4()),
                type=ConflictType.TEMPORAL_CONTRADICTION,
                description=f"Incohérence temporelle au {inconsistency.date}.",
                explanation=inconsistency.reason,
                involved_ids=tuple(
                    doc_id
                    for entry in inconsistency.entries
                    for doc_id in entry.document_ids
                ),
            )
            for inconsistency in timeline_inconsistencies
        ]

    def _duplicates(self, facts: list[Fact]) -> list[Conflict]:
        by_description: dict[str, list[Fact]] = defaultdict(list)
        for fact in facts:
            by_description[fact.description.strip().lower()].append(fact)

        return [
            Conflict(
                id=str(uuid.uuid4()),
                type=ConflictType.DUPLICATE,
                description=f"{len(group)} faits en double pour « {group[0].description} ».",
                explanation="Plusieurs faits distincts partagent la même description normalisée.",
                involved_ids=tuple(fact.id for fact in group),
            )
            for group in by_description.values()
            if len(group) > 1
        ]
