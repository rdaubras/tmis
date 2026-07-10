from tmis.collaboration.workspace.schemas import Workspace


class InMemoryWorkspaceStore:
    """Implements `WorkspaceStorePort` with an in-memory dict — the
    default deployment for Sprint 8; persistence follows the same
    calendar as the rest of TMIS's engines (Sprint 9)."""

    def __init__(self) -> None:
        self._workspaces: dict[str, Workspace] = {}

    def get(self, workspace_id: str) -> Workspace | None:
        return self._workspaces.get(workspace_id)

    def save(self, workspace: Workspace) -> None:
        self._workspaces[workspace.id] = workspace

    def list_for_firm(self, firm_id: str) -> list[Workspace]:
        return [w for w in self._workspaces.values() if w.firm_id == firm_id]

    def list_ids(self) -> list[str]:
        return list(self._workspaces)
