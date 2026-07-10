from tmis.collaboration.members.schemas import Member


class InMemoryMemberStore:
    """Implements `MemberStorePort` with an in-memory dict."""

    def __init__(self) -> None:
        self._members: dict[str, Member] = {}

    def get(self, member_id: str) -> Member | None:
        return self._members.get(member_id)

    def save(self, member: Member) -> None:
        self._members[member.id] = member

    def list_for_workspace(self, workspace_id: str) -> list[Member]:
        return [m for m in self._members.values() if m.workspace_id == workspace_id]
