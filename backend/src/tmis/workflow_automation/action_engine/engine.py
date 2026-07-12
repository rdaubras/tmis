from tmis.workflow_automation.action_engine.ports import ActionHandlerPort, ActionLogStorePort
from tmis.workflow_automation.action_engine.schemas import (
    Action,
    ActionLogEntry,
    ActionResult,
    new_action_log_id,
)


class UnknownActionTypeError(KeyError):
    pass


class ActionEngine:
    """Runs the registered handler for an action's type and always
    journals the result, success or failure — every execution is
    traceable back to the workflow execution that triggered it."""

    def __init__(
        self, store: ActionLogStorePort, handlers: list[ActionHandlerPort] | None = None
    ) -> None:
        self._store = store
        self._handlers: dict[str, ActionHandlerPort] = {
            h.action_type: h for h in (handlers or [])
        }

    def register(self, handler: ActionHandlerPort) -> None:
        self._handlers[handler.action_type] = handler

    def execute(
        self, firm_id: str, execution_id: str, action: Action, context: dict[str, str]
    ) -> ActionResult:
        handler = self._handlers.get(action.action_type)
        if handler is None:
            raise UnknownActionTypeError(action.action_type)
        try:
            result = handler.execute(action, context)
        except Exception as exc:  # noqa: BLE001 - always journaled, never swallowed silently
            result = ActionResult(success=False, detail=str(exc))
        self._store.add(
            ActionLogEntry(
                id=new_action_log_id(),
                firm_id=firm_id,
                execution_id=execution_id,
                action_id=action.id,
                action_type=action.action_type,
                result=result,
            )
        )
        return result

    def history_for_execution(self, firm_id: str, execution_id: str) -> list[ActionLogEntry]:
        return self._store.list_for_execution(firm_id, execution_id)
