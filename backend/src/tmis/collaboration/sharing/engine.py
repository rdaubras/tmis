import secrets
import uuid
from datetime import UTC, datetime, timedelta

from tmis.collaboration.sharing.ports import SharingStorePort
from tmis.collaboration.sharing.schemas import InternalShare, ShareLink, SharePermission


class SharingEngine:
    """Implements `SharingEnginePort` (see docs/33-legal-collaboration.md
    — Sharing Engine): internal shares grant access to another member
    directly; share links are bearer tokens for external recipients,
    optionally time-limited, always revocable."""

    def __init__(self, store: SharingStorePort) -> None:
        self._store = store

    def share_internally(
        self,
        workspace_id: str,
        target_type: str,
        target_id: str,
        shared_with_member_id: str,
        permission: SharePermission,
        created_by: str,
    ) -> InternalShare:
        share = InternalShare(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            target_type=target_type,
            target_id=target_id,
            shared_with_member_id=shared_with_member_id,
            permission=permission,
            created_by=created_by,
            created_at=datetime.now(UTC),
        )
        self._store.save_internal_share(share)
        return share

    def create_link(
        self,
        workspace_id: str,
        target_type: str,
        target_id: str,
        permission: SharePermission,
        created_by: str,
        expires_in_seconds: int | None = None,
    ) -> ShareLink:
        now = datetime.now(UTC)
        link = ShareLink(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            target_type=target_type,
            target_id=target_id,
            token=secrets.token_urlsafe(32),
            permission=permission,
            created_by=created_by,
            created_at=now,
            expires_at=(
                now + timedelta(seconds=expires_in_seconds)
                if expires_in_seconds is not None
                else None
            ),
        )
        self._store.save_link(link)
        return link

    def revoke_link(self, token: str) -> ShareLink:
        link = self._store.get_link_by_token(token)
        if link is None:
            raise ValueError(f"Unknown share link {token!r}")
        link.revoked_at = datetime.now(UTC)
        self._store.save_link(link)
        return link

    def resolve_link(self, token: str) -> ShareLink | None:
        link = self._store.get_link_by_token(token)
        if link is None or link.revoked_at is not None:
            return None
        if link.expires_at is not None and link.expires_at < datetime.now(UTC):
            return None
        return link

    def list_for_target(self, target_type: str, target_id: str) -> list[InternalShare]:
        return self._store.list_for_target(target_type, target_id)
