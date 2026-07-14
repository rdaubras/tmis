from tmis.legal_knowledge_graph.entity_resolution.schemas import ResolutionMatch


class InMemoryResolutionMatchStore:
    """Keeps every version of a match ever saved — `decide()` in the
    engine appends a new record rather than mutating history away, so
    "historique" (sprint requirement) is never lost."""

    def __init__(self) -> None:
        self._history: dict[str, list[ResolutionMatch]] = {}

    def save(self, match: ResolutionMatch) -> None:
        self._history.setdefault(match.id, []).append(match)

    def get_latest(self, firm_id: str, match_id: str) -> ResolutionMatch | None:
        versions = self._history.get(match_id)
        if not versions:
            return None
        latest = versions[-1]
        return latest if latest.firm_id == firm_id else None

    def history(self, firm_id: str, match_id: str) -> list[ResolutionMatch]:
        return [m for m in self._history.get(match_id, []) if m.firm_id == firm_id]

    def list_for_firm(self, firm_id: str) -> list[ResolutionMatch]:
        return [
            versions[-1] for versions in self._history.values() if versions[-1].firm_id == firm_id
        ]
