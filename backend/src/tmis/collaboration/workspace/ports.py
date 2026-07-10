from typing import Protocol

from tmis.collaboration.workspace.schemas import Workspace


class WorkspaceStorePort(Protocol):
    """Port implemented by every interchangeable workspace store."""

    def get(self, workspace_id: str) -> Workspace | None: ...

    def save(self, workspace: Workspace) -> None: ...

    def list_for_firm(self, firm_id: str) -> list[Workspace]: ...

    def list_ids(self) -> list[str]: ...
