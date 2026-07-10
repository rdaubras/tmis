from typing import Protocol

from tmis.collaboration.members.schemas import Member


class MemberStorePort(Protocol):
    """Port implemented by every interchangeable member store."""

    def get(self, member_id: str) -> Member | None: ...

    def save(self, member: Member) -> None: ...

    def list_for_workspace(self, workspace_id: str) -> list[Member]: ...


class MemberServicePort(Protocol):
    """Port implemented by every interchangeable member lifecycle
    service."""

    def invite(self, workspace_id: str, email: str, display_name: str) -> Member: ...

    def activate(self, member_id: str, actor_id: str | None = None) -> Member: ...

    def suspend(self, member_id: str, actor_id: str | None = None) -> Member: ...

    def deactivate(self, member_id: str, actor_id: str | None = None) -> Member: ...

    def reactivate(self, member_id: str, actor_id: str | None = None) -> Member: ...
