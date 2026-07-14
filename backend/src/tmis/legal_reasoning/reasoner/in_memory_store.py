from tmis.legal_reasoning.reasoner.schemas import ReasoningSession


class InMemorySessionStore:
    """Implements `SessionStorePort` with a process-local dict — the
    default backend for `ReasoningOrchestrator` (Sprint 26), replacing its
    former private `dict` one-for-one so existing behavior is unchanged
    unless a real store (`SQLAlchemySessionStore`) is injected."""

    def __init__(self) -> None:
        self._sessions: dict[str, ReasoningSession] = {}

    def get(self, session_id: str) -> ReasoningSession | None:
        return self._sessions.get(session_id)

    def save(self, session: ReasoningSession) -> None:
        self._sessions[session.id] = session

    def list_ids(self) -> list[str]:
        return list(self._sessions)
