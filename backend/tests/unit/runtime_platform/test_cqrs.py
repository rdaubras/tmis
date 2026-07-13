import asyncio
from dataclasses import dataclass

import pytest

from tmis.runtime_platform.cqrs.engine import (
    CommandBus,
    HandlerAlreadyRegisteredError,
    NoHandlerRegisteredError,
    QueryBus,
)


@dataclass
class CreateWidget:
    name: str


@dataclass
class GetWidgetCount:
    pass


def test_command_bus_dispatches_to_registered_handler() -> None:
    async def scenario() -> None:
        bus = CommandBus()
        created: list[str] = []

        async def handler(command: CreateWidget) -> str:
            created.append(command.name)
            return "widget-1"

        bus.register(CreateWidget, handler)
        result = await bus.dispatch(CreateWidget(name="gadget"))

        assert result == "widget-1"
        assert created == ["gadget"]

    asyncio.run(scenario())


def test_command_bus_rejects_second_handler_for_same_type() -> None:
    bus = CommandBus()

    async def handler(command: CreateWidget) -> None:
        return None

    bus.register(CreateWidget, handler)
    with pytest.raises(HandlerAlreadyRegisteredError):
        bus.register(CreateWidget, handler)


def test_command_bus_raises_for_unregistered_type() -> None:
    async def scenario() -> None:
        bus = CommandBus()
        with pytest.raises(NoHandlerRegisteredError):
            await bus.dispatch(CreateWidget(name="gadget"))

    asyncio.run(scenario())


def test_query_bus_asks_registered_handler() -> None:
    async def scenario() -> None:
        bus = QueryBus()

        async def handler(_query: GetWidgetCount) -> int:
            return 42

        bus.register(GetWidgetCount, handler)
        result = await bus.ask(GetWidgetCount())

        assert result == 42

    asyncio.run(scenario())
