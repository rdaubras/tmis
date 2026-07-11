from tmis.strategic_intelligence.hypothesis_lab.schemas import (
    HypothesisEvent,
    StrategicHypothesis,
)


class InMemoryHypothesisLabStore:
    def __init__(self) -> None:
        self._hypotheses: dict[tuple[str, str], StrategicHypothesis] = {}
        self._events: list[HypothesisEvent] = []

    def add(self, firm_id: str, hypothesis: StrategicHypothesis) -> None:
        self._hypotheses[(firm_id, hypothesis.id)] = hypothesis

    def get(self, firm_id: str, hypothesis_id: str) -> StrategicHypothesis | None:
        return self._hypotheses.get((firm_id, hypothesis_id))

    def list_for_case(self, firm_id: str, case_id: str) -> list[StrategicHypothesis]:
        return [
            h
            for (fid, _), h in self._hypotheses.items()
            if fid == firm_id and h.case_id == case_id
        ]

    def append_event(self, event: HypothesisEvent) -> None:
        self._events.append(event)

    def history(self, firm_id: str, hypothesis_id: str) -> list[HypothesisEvent]:
        return [
            e
            for e in self._events
            if e.firm_id == firm_id and e.hypothesis_id == hypothesis_id
        ]
