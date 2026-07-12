from typing import Protocol

from tmis.workflow_automation.action_engine.schemas import Action
from tmis.workflow_automation.rollback.schemas import RollbackLogEntry, RollbackResult


class RollbackHandlerPort(Protocol):
    """One pluggable compensation handler for a reversible action
    type. Not every action type is reversible — an action with no
    registered handler simply cannot be rolled back, and
    `RollbackEngine.rollback` reports that explicitly rather than
    silently no-op'ing."""

    action_type: str

    def compensate(self, action: Action, context: dict[str, str]) -> RollbackResult: ...


class RollbackLogStorePort(Protocol):
    def add(self, entry: RollbackLogEntry) -> None: ...

    def list_for_execution(self, firm_id: str, execution_id: str) -> list[RollbackLogEntry]: ...
