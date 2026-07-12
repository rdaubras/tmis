from typing import Protocol

from tmis.workflow_automation.action_engine.schemas import Action, ActionLogEntry, ActionResult


class ActionHandlerPort(Protocol):
    """One pluggable action executor. `ActionEngine` is closed over
    this narrow contract so a new action type — or a real integration
    behind `ACTION_CALL_INTEGRATION` — can be registered without
    touching the engine."""

    action_type: str

    def execute(self, action: Action, context: dict[str, str]) -> ActionResult: ...


class ActionLogStorePort(Protocol):
    def add(self, entry: ActionLogEntry) -> None: ...

    def list_for_execution(self, firm_id: str, execution_id: str) -> list[ActionLogEntry]: ...
