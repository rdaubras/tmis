from tmis.identity_platform.impersonation.schemas import ImpersonationSession


class InMemoryImpersonationStore:
    def __init__(self) -> None:
        self._sessions: dict[tuple[str, str], ImpersonationSession] = {}

    def save(self, session: ImpersonationSession) -> None:
        self._sessions[(session.firm_id, session.id)] = session

    def get(self, firm_id: str, session_id: str) -> ImpersonationSession | None:
        return self._sessions.get((firm_id, session_id))

    def active_for_admin(self, firm_id: str, admin_id: str) -> ImpersonationSession | None:
        for session in self._sessions.values():
            if (
                session.firm_id == firm_id
                and session.admin_id == admin_id
                and session.ended_at is None
            ):
                return session
        return None

    def list_for_firm(self, firm_id: str) -> list[ImpersonationSession]:
        return [s for s in self._sessions.values() if s.firm_id == firm_id]
