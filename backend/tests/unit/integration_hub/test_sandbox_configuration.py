import asyncio

import pytest

from tmis.integration_hub.configuration import (
    ConfigurationEngine,
    ConfigurationValidationError,
    InMemoryConnectorConfigurationStore,
)
from tmis.integration_hub.connector_framework import ConnectorCapability, ConnectorType
from tmis.integration_hub.connector_registry import ConnectorDescriptor
from tmis.integration_hub.sandbox import ConnectorResourceQuota, ConnectorSandbox


@pytest.mark.asyncio
async def test_sandbox_run_success() -> None:
    sandbox = ConnectorSandbox()

    async def op() -> dict[str, int]:
        return {"value": 42}

    result = await sandbox.run("f1", "c1", op)
    assert result.success is True
    assert result.result == {"value": 42}


@pytest.mark.asyncio
async def test_sandbox_quota_enforced() -> None:
    sandbox = ConnectorSandbox(ConnectorResourceQuota(max_calls_per_minute=1))

    async def op() -> None:
        return None

    first = await sandbox.run("f1", "c1", op)
    assert first.success is True
    second = await sandbox.run("f1", "c1", op)
    assert second.success is False
    assert "quota" in (second.error or "")


@pytest.mark.asyncio
async def test_sandbox_timeout_enforced() -> None:
    sandbox = ConnectorSandbox(ConnectorResourceQuota(max_execution_seconds=0.01))

    async def slow() -> None:
        await asyncio.sleep(1)

    result = await sandbox.run("f1", "c1", slow)
    assert result.success is False
    assert "délai" in (result.error or "")


@pytest.mark.asyncio
async def test_sandbox_catches_exceptions() -> None:
    sandbox = ConnectorSandbox()

    async def boom() -> None:
        raise ValueError("kaboom")

    result = await sandbox.run("f1", "c1", boom)
    assert result.success is False
    assert result.error == "kaboom"


def test_configuration_engine_set_and_get() -> None:
    store = InMemoryConnectorConfigurationStore()
    engine = ConfigurationEngine(store)

    config = engine.set_configuration("c1", "f1", {"api_key": "xyz"})
    fetched = engine.get_configuration("f1", "c1")
    assert fetched is config
    assert fetched.values == {"api_key": "xyz"}


def test_configuration_engine_validates_against_descriptor_schema() -> None:
    store = InMemoryConnectorConfigurationStore()
    engine = ConfigurationEngine(store)
    descriptor = ConnectorDescriptor(
        id="c1", name="Fake", version="1.0", publisher="TMIS",
        connector_type=ConnectorType.CRM, capabilities=frozenset({ConnectorCapability.READ}),
        config_schema={"api_key": "string"},
    )

    with pytest.raises(ConfigurationValidationError):
        engine.set_configuration("c1", "f1", {}, descriptor)

    config = engine.set_configuration("c1", "f1", {"api_key": "xyz"}, descriptor)
    assert config.values == {"api_key": "xyz"}


def test_configuration_engine_get_missing_returns_none() -> None:
    store = InMemoryConnectorConfigurationStore()
    engine = ConfigurationEngine(store)
    assert engine.get_configuration("f1", "missing") is None
