from typing import Protocol

from tmis.collaboration.sharing.schemas import InternalShare, ShareLink, SharePermission


class SharingStorePort(Protocol):
    def save_internal_share(self, share: InternalShare) -> None: ...

    def save_link(self, link: ShareLink) -> None: ...

    def get_link_by_token(self, token: str) -> ShareLink | None: ...

    def list_for_target(self, target_type: str, target_id: str) -> list[InternalShare]: ...

    def list_links_for_target(self, target_type: str, target_id: str) -> list[ShareLink]: ...


class SharingEnginePort(Protocol):
    """Port implemented by every interchangeable sharing engine."""

    def share_internally(
        self,
        workspace_id: str,
        target_type: str,
        target_id: str,
        shared_with_member_id: str,
        permission: SharePermission,
        created_by: str,
    ) -> InternalShare: ...

    def create_link(
        self,
        workspace_id: str,
        target_type: str,
        target_id: str,
        permission: SharePermission,
        created_by: str,
        expires_in_seconds: int | None = None,
    ) -> ShareLink: ...

    def revoke_link(self, token: str) -> ShareLink: ...

    def resolve_link(self, token: str) -> ShareLink | None: ...

    def list_for_target(self, target_type: str, target_id: str) -> list[InternalShare]: ...
