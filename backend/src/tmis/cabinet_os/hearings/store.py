from tmis.cabinet_os.hearings.schemas import Hearing


class InMemoryHearingStore:
    """Implements `HearingStorePort` with an in-memory dict."""

    def __init__(self) -> None:
        self._hearings: dict[str, Hearing] = {}

    def get(self, hearing_id: str) -> Hearing | None:
        return self._hearings.get(hearing_id)

    def save(self, hearing: Hearing) -> None:
        self._hearings[hearing.id] = hearing

    def list_for_case(self, case_id: str) -> list[Hearing]:
        return [h for h in self._hearings.values() if h.case_id == case_id]

    def list_for_firm(self, firm_id: str) -> list[Hearing]:
        return [h for h in self._hearings.values() if h.firm_id == firm_id]
