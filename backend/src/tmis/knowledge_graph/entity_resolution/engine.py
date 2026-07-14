from collections.abc import Sequence
from difflib import SequenceMatcher

from tmis.ai_governance.human_validation.engine import HumanValidationEngine
from tmis.ai_governance.human_validation.schemas import ValidationDecisionType, ValidationStatus
from tmis.knowledge_graph.entity_resolution.ports import ResolvedEntityStorePort
from tmis.knowledge_graph.entity_resolution.schemas import (
    EntityOccurrence,
    ResolutionStatus,
    ResolvedEntity,
    new_resolved_entity_id,
)

_STATUS_FOR_DECISION: dict[ValidationStatus, ResolutionStatus] = {
    ValidationStatus.APPROVED: ResolutionStatus.CONFIRMED,
    ValidationStatus.REJECTED: ResolutionStatus.REJECTED,
    ValidationStatus.PENDING: ResolutionStatus.PENDING_VALIDATION,
    ValidationStatus.REVISION_REQUESTED: ResolutionStatus.PENDING_VALIDATION,
}


def _normalize(label: str) -> str:
    return " ".join(label.casefold().split())


def _label_similarity(occurrences: Sequence[EntityOccurrence]) -> float:
    """The weakest pairwise match across every occurrence's label —
    conservative on purpose: one poorly-matching pair is enough to
    make the whole group's confidence low, since a resolved entity is
    only as trustworthy as its worst-matched occurrence."""
    if len(occurrences) < 2:
        return 1.0
    labels = [_normalize(o.label) for o in occurrences]
    scores = [
        SequenceMatcher(None, labels[i], labels[j]).ratio()
        for i in range(len(labels))
        for j in range(i + 1, len(labels))
    ]
    return min(scores)


class EntityResolutionEngine:
    """Resolves that occurrences from the three existing graphs
    denote the same real-world entity. Never stores graph nodes/edges
    — only the resolution outcome (`ResolvedEntity`) itself. Below
    `confidence_threshold`, resolution is never auto-confirmed: it is
    routed through `HumanValidationEngine` (simple mode — one approver
    settles it), the same engine every other bounded context in TMIS
    uses for human validation.
    """

    def __init__(
        self,
        store: ResolvedEntityStorePort,
        human_validation: HumanValidationEngine,
        confidence_threshold: float = 0.85,
    ) -> None:
        self._store = store
        self._human_validation = human_validation
        self._confidence_threshold = confidence_threshold

    def resolve(
        self,
        firm_id: str,
        requested_by: str,
        occurrences: Sequence[EntityOccurrence],
        approver_ids: tuple[str, ...] = (),
    ) -> ResolvedEntity:
        confidence = _label_similarity(occurrences)
        entity_id = new_resolved_entity_id()
        validation_request_id: str | None = None

        if confidence < self._confidence_threshold:
            status = ResolutionStatus.PENDING_VALIDATION
            request = self._human_validation.request_simple(
                firm_id, entity_id, requested_by, approver_ids
            )
            validation_request_id = request.id
        else:
            status = ResolutionStatus.CONFIRMED

        entity = ResolvedEntity(
            id=entity_id,
            firm_id=firm_id,
            occurrences=tuple(occurrences),
            confidence=confidence,
            status=status,
            validation_request_id=validation_request_id,
        )
        self._store.save(entity)
        return entity

    def decide(
        self, firm_id: str, entity_id: str, approver_id: str, decision: ValidationDecisionType
    ) -> ResolvedEntity:
        entity = self._store.get(firm_id, entity_id)
        if entity is None:
            raise KeyError(entity_id)
        if entity.validation_request_id is None:
            raise ValueError(f"resolved entity {entity_id} has no pending human validation")

        request = self._human_validation.decide(
            firm_id, entity.validation_request_id, approver_id, decision
        )
        entity.status = _STATUS_FOR_DECISION[request.status]
        self._store.save(entity)
        return entity

    def get(self, firm_id: str, entity_id: str) -> ResolvedEntity | None:
        return self._store.get(firm_id, entity_id)

    def list_for_firm(self, firm_id: str) -> list[ResolvedEntity]:
        return self._store.list_for_firm(firm_id)
