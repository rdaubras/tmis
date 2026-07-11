from tmis.workflow_automation.action_engine.schemas import Action
from tmis.workflow_automation.rollback.ports import RollbackHandlerPort, RollbackLogStorePort
from tmis.workflow_automation.rollback.schemas import (
    RollbackLogEntry,
    RollbackResult,
    new_rollback_log_id,
)


class RollbackEngine:
    """Compensates reversible actions and journals every attempt."""

    def __init__(
        self, store: RollbackLogStorePort, handlers: list[RollbackHandlerPort] | None = None
    ) -> None:
        self._store = store
        self._handlers: dict[str, RollbackHandlerPort] = {
            h.action_type: h for h in (handlers or [])
        }

    def register(self, handler: RollbackHandlerPort) -> None:
        self._handlers[handler.action_type] = handler

    def rollback(
        self, firm_id: str, execution_id: str, action: Action, context: dict[str, str]
    ) -> RollbackResult:
        handler = self._handlers.get(action.action_type)
        if handler is None:
            result = RollbackResult(
                compensated=False,
                detail=f"No rollback handler registered for {action.action_type!r}",
            )
        else:
            try:
                result = handler.compensate(action, context)
            except Exception as exc:  # noqa: BLE001 - always journaled
                result = RollbackResult(compensated=False, detail=str(exc))
        self._store.add(
            RollbackLogEntry(
                id=new_rollback_log_id(),
                firm_id=firm_id,
                execution_id=execution_id,
                action_id=action.id,
                action_type=action.action_type,
                result=result,
            )
        )
        return result

    def history_for_execution(self, firm_id: str, execution_id: str) -> list[RollbackLogEntry]:
        return self._store.list_for_execution(firm_id, execution_id)
