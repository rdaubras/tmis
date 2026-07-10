from tmis.collaboration.sharing.schemas import InternalShare, ShareLink


class InMemorySharingStore:
    """Implements `SharingStorePort` with in-memory dicts."""

    def __init__(self) -> None:
        self._shares: dict[str, InternalShare] = {}
        self._links: dict[str, ShareLink] = {}

    def save_internal_share(self, share: InternalShare) -> None:
        self._shares[share.id] = share

    def save_link(self, link: ShareLink) -> None:
        self._links[link.token] = link

    def get_link_by_token(self, token: str) -> ShareLink | None:
        return self._links.get(token)

    def list_for_target(self, target_type: str, target_id: str) -> list[InternalShare]:
        return [
            s
            for s in self._shares.values()
            if s.target_type == target_type and s.target_id == target_id
        ]

    def list_links_for_target(self, target_type: str, target_id: str) -> list[ShareLink]:
        return [
            link
            for link in self._links.values()
            if link.target_type == target_type and link.target_id == target_id
        ]
