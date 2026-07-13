from collections.abc import Awaitable, Callable
from typing import Any

Handler = Callable[[Any], Awaitable[Any]]


class HandlerAlreadyRegisteredError(ValueError):
    pass


class NoHandlerRegisteredError(KeyError):
    pass


class _TypeDispatchBus:
    """Shared dispatch shape for `CommandBus` and `QueryBus`: exactly
    one handler per message type, matching the CQRS convention that a
    command/query has a single owner (unlike an event, which may have
    many subscribers on the existing event buses)."""

    def __init__(self, kind: str) -> None:
        self._kind = kind
        self._handlers: dict[type, Handler] = {}

    def register(self, message_type: type, handler: Handler) -> None:
        if message_type in self._handlers:
            raise HandlerAlreadyRegisteredError(
                f"a {self._kind} handler is already registered for {message_type.__name__}"
            )
        self._handlers[message_type] = handler

    async def _dispatch(self, message: Any) -> Any:
        handler = self._handlers.get(type(message))
        if handler is None:
            raise NoHandlerRegisteredError(
                f"no {self._kind} handler registered for {type(message).__name__}"
            )
        return await handler(message)


class CommandBus(_TypeDispatchBus):
    """CQRS command bus foundation. `dispatch` runs the single
    registered handler for a command's type and returns whatever it
    returns (typically nothing, or a created entity's id) — no
    domain is migrated onto this by this sprint; it's available for
    progressive adoption."""

    def __init__(self) -> None:
        super().__init__("command")

    async def dispatch(self, command: Any) -> Any:
        return await self._dispatch(command)


class QueryBus(_TypeDispatchBus):
    """CQRS query bus foundation — same single-handler-per-type
    dispatch as `CommandBus`, named `ask` to read naturally at call
    sites (`await query_bus.ask(GetInvoiceById(...))`)."""

    def __init__(self) -> None:
        super().__init__("query")

    async def ask(self, query: Any) -> Any:
        return await self._dispatch(query)
