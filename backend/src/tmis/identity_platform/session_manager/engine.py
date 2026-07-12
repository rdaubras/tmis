from datetime import UTC, datetime

from tmis.identity_platform.session_manager.ports import SessionStorePort
from tmis.identity_platform.session_manager.schemas import (
    Session,
    new_refresh_token,
    new_session_id,
)


class SessionManager:
    """Multiple concurrent sessions per user, expiration, revocation
    (single session or every session of a user) and refresh-token
    rotation — "sessions multiples, expiration, révocation, appareils
    de confiance, historique, rotation des jetons" (sprint
    requirement). `device_trust` is composed by the caller (a
    `device_id` is accepted, never resolved here) so this module
    stays independent of how a device was identified."""

    def __init__(self, store: SessionStorePort) -> None:
        self._store = store

    def create(self, firm_id: str, user_id: str, device_id: str | None = None) -> Session:
        session = Session(
            id=new_session_id(),
            firm_id=firm_id,
            user_id=user_id,
            device_id=device_id,
            refresh_token=new_refresh_token(),
        )
        self._store.save(session)
        return session

    def is_active(self, firm_id: str, session_id: str) -> bool:
        session = self._store.get(firm_id, session_id)
        if session is None or session.revoked:
            return False
        return session.expires_at > datetime.now(UTC)

    def revoke(self, firm_id: str, session_id: str) -> Session:
        session = self._get(firm_id, session_id)
        session.revoked = True
        self._store.save(session)
        return session

    def revoke_all_for_user(self, firm_id: str, user_id: str) -> list[Session]:
        revoked = []
        for session in self._store.list_for_user(firm_id, user_id):
            session.revoked = True
            self._store.save(session)
            revoked.append(session)
        return revoked

    def rotate_refresh_token(self, firm_id: str, session_id: str) -> str:
        session = self._get(firm_id, session_id)
        session.refresh_token = new_refresh_token()
        self._store.save(session)
        return session.refresh_token

    def list_for_user(self, firm_id: str, user_id: str) -> list[Session]:
        return self._store.list_for_user(firm_id, user_id)

    def list_for_firm(self, firm_id: str) -> list[Session]:
        return self._store.list_for_firm(firm_id)

    def _get(self, firm_id: str, session_id: str) -> Session:
        session = self._store.get(firm_id, session_id)
        if session is None:
            raise KeyError(session_id)
        return session
