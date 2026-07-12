from datetime import UTC, datetime

from tmis.identity_platform.impersonation.ports import ImpersonationStorePort
from tmis.identity_platform.impersonation.schemas import ImpersonationSession, new_impersonation_id


class ImpersonationEngine:
    """Admin-assists-user support sessions — "toutes les opérations
    sont journalisées, limitées, visibles, auditables" (sprint
    requirement). `start` refuses a second concurrent impersonation by
    the same admin (limited), and every session is a durable,
    listable record that never disappears (auditable) — closing a
    session sets `ended_at`, it is never deleted."""

    def __init__(self, store: ImpersonationStorePort) -> None:
        self._store = store

    def start(
        self, firm_id: str, admin_id: str, target_user_id: str, reason: str
    ) -> ImpersonationSession:
        if self._store.active_for_admin(firm_id, admin_id) is not None:
            raise RuntimeError(f"admin {admin_id!r} already has an active impersonation session")
        session = ImpersonationSession(
            id=new_impersonation_id(),
            firm_id=firm_id,
            admin_id=admin_id,
            target_user_id=target_user_id,
            reason=reason,
        )
        self._store.save(session)
        return session

    def end(self, firm_id: str, session_id: str) -> ImpersonationSession:
        session = self._store.get(firm_id, session_id)
        if session is None:
            raise KeyError(session_id)
        session.ended_at = datetime.now(UTC)
        self._store.save(session)
        return session

    def active_for_admin(self, firm_id: str, admin_id: str) -> ImpersonationSession | None:
        return self._store.active_for_admin(firm_id, admin_id)

    def history(self, firm_id: str) -> list[ImpersonationSession]:
        return self._store.list_for_firm(firm_id)
