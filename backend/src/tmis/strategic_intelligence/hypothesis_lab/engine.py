from __future__ import annotations

from tmis.strategic_intelligence.hypothesis_lab.ports import HypothesisLabStorePort
from tmis.strategic_intelligence.hypothesis_lab.schemas import (
    ALLOWED_TRANSITIONS,
    HypothesisComparison,
    HypothesisEvent,
    HypothesisStatus,
    InvalidHypothesisTransitionError,
    StrategicHypothesis,
    new_hypothesis_event_id,
    new_hypothesis_id,
)


class HypothesisLabEngine:
    """Historized lifecycle: create / compare / merge / invalidate / archive.

    Only place allowed to mutate `StrategicHypothesis.status`; every
    mutation is recorded as a `HypothesisEvent`, mirroring
    `tmis.cabinet_knowledge.governance.GovernanceEngine`.
    """

    def __init__(self, store: HypothesisLabStorePort) -> None:
        self._store = store

    def create(
        self,
        firm_id: str,
        case_id: str,
        description: str,
        parent_ids: tuple[str, ...] = (),
    ) -> StrategicHypothesis:
        hypothesis = StrategicHypothesis(
            id=new_hypothesis_id(),
            case_id=case_id,
            description=description,
            parent_ids=parent_ids,
        )
        self._store.add(firm_id, hypothesis)
        return hypothesis

    def get(self, firm_id: str, hypothesis_id: str) -> StrategicHypothesis:
        hypothesis = self._store.get(firm_id, hypothesis_id)
        if hypothesis is None:
            raise KeyError(hypothesis_id)
        return hypothesis

    def list_for_case(self, firm_id: str, case_id: str) -> list[StrategicHypothesis]:
        return self._store.list_for_case(firm_id, case_id)

    def compare(
        self, firm_id: str, hypothesis_a_id: str, hypothesis_b_id: str
    ) -> HypothesisComparison:
        a = self.get(firm_id, hypothesis_a_id)
        b = self.get(firm_id, hypothesis_b_id)
        words_a = {w.lower() for w in a.description.split()}
        words_b = {w.lower() for w in b.description.split()}
        shared = words_a & words_b
        union = words_a | words_b
        similarity = round(len(shared) / len(union), 2) if union else 0.0
        differences = tuple(sorted(words_a ^ words_b))
        return HypothesisComparison(
            hypothesis_a_id=hypothesis_a_id,
            hypothesis_b_id=hypothesis_b_id,
            similarity=similarity,
            shared_terms=tuple(sorted(shared)),
            differences=differences,
        )

    def merge(
        self,
        firm_id: str,
        hypothesis_a_id: str,
        hypothesis_b_id: str,
        actor: str,
        merged_description: str | None = None,
    ) -> StrategicHypothesis:
        a = self.get(firm_id, hypothesis_a_id)
        b = self.get(firm_id, hypothesis_b_id)
        description = merged_description or f"{a.description} / {b.description}"
        merged = self.create(
            firm_id, a.case_id, description, parent_ids=(hypothesis_a_id, hypothesis_b_id)
        )
        self._transition(firm_id, a, HypothesisStatus.MERGED, actor, reason="Fusionnée")
        self._transition(firm_id, b, HypothesisStatus.MERGED, actor, reason="Fusionnée")
        return merged

    def invalidate(
        self, firm_id: str, hypothesis_id: str, actor: str, reason: str
    ) -> StrategicHypothesis:
        hypothesis = self.get(firm_id, hypothesis_id)
        self._transition(firm_id, hypothesis, HypothesisStatus.INVALIDATED, actor, reason)
        return hypothesis

    def support(self, firm_id: str, hypothesis_id: str, actor: str) -> StrategicHypothesis:
        hypothesis = self.get(firm_id, hypothesis_id)
        self._transition(
            firm_id,
            hypothesis,
            HypothesisStatus.SUPPORTED,
            actor,
            reason="Élément de soutien ajouté",
        )
        return hypothesis

    def archive(
        self, firm_id: str, hypothesis_id: str, actor: str, reason: str | None = None
    ) -> StrategicHypothesis:
        hypothesis = self.get(firm_id, hypothesis_id)
        self._transition(firm_id, hypothesis, HypothesisStatus.ARCHIVED, actor, reason)
        return hypothesis

    def history(self, firm_id: str, hypothesis_id: str) -> list[HypothesisEvent]:
        return self._store.history(firm_id, hypothesis_id)

    def _transition(
        self,
        firm_id: str,
        hypothesis: StrategicHypothesis,
        to_status: HypothesisStatus,
        actor: str,
        reason: str | None,
    ) -> None:
        if to_status not in ALLOWED_TRANSITIONS[hypothesis.status]:
            raise InvalidHypothesisTransitionError(hypothesis.status, to_status)
        from_status = hypothesis.status
        hypothesis.status = to_status
        self._store.append_event(
            HypothesisEvent(
                id=new_hypothesis_event_id(),
                firm_id=firm_id,
                hypothesis_id=hypothesis.id,
                from_status=from_status,
                to_status=to_status,
                actor=actor,
                reason=reason,
            )
        )
