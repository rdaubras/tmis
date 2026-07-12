from tmis.identity_platform.session_manager.schemas import Session


class InMemorySessionStore:
    def __init__(self) -> None:
        self._sessions: dict[tuple[str, str], Session] = {}

    def save(self, session: Session) -> None:
        self._sessions[(session.firm_id, session.id)] = session

    def get(self, firm_id: str, session_id: str) -> Session | None:
        return self._sessions.get((firm_id, session_id))

    def list_for_user(self, firm_id: str, user_id: str) -> list[Session]:
        return [s for s in self._sessions.values() if s.firm_id == firm_id and s.user_id == user_id]

    def list_for_firm(self, firm_id: str) -> list[Session]:
        return [s for s in self._sessions.values() if s.firm_id == firm_id]
