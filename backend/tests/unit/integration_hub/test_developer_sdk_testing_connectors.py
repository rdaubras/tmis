import pytest

from tmis.integration_hub.connector_framework import (
    ConnectorCapability,
    ConnectorInvoker,
    ConnectorRecord,
    ConnectorType,
)
from tmis.integration_hub.connector_registry import (
    ConnectorRegistryEngine,
    InMemoryConnectorRegistryStore,
)
from tmis.integration_hub.connectors import (
    DemoBillingConnector,
    DemoCalendarConnector,
    DemoCrmConnector,
    DemoDmsConnector,
    DemoDocumentStorageConnector,
    DemoESignatureConnector,
    DemoMessagingConnector,
)
from tmis.integration_hub.developer_sdk import BaseConnector, register_connector
from tmis.integration_hub.testing import (
    ConnectorConformanceError,
    InMemoryFakeConnector,
    NoOpMetricsRecorder,
    assert_connector_conforms,
)

_ALL_DEMO_CONNECTORS = (
    DemoMessagingConnector,
    DemoCalendarConnector,
    DemoDocumentStorageConnector,
    DemoESignatureConnector,
    DemoDmsConnector,
    DemoBillingConnector,
    DemoCrmConnector,
)


class _MinimalConnector(BaseConnector):
    connector_type = ConnectorType.CRM
    capabilities = frozenset({ConnectorCapability.READ})

    async def read(
        self, config: dict[str, str], since: str | None = None
    ) -> list[ConnectorRecord]:
        return [ConnectorRecord(external_id="e1", data={"name": "demo"})]


@pytest.mark.asyncio
async def test_base_connector_default_authenticate_returns_true() -> None:
    connector = _MinimalConnector()
    assert await connector.authenticate({}) is True


@pytest.mark.asyncio
async def test_base_connector_unimplemented_write_raises() -> None:
    connector = _MinimalConnector()
    with pytest.raises(NotImplementedError):
        await connector.write({}, ConnectorRecord(external_id="e1", data={}))


@pytest.mark.asyncio
async def test_base_connector_conforms() -> None:
    await assert_connector_conforms(_MinimalConnector(), {})


def test_register_connector_builds_descriptor_from_implementation() -> None:
    registry = ConnectorRegistryEngine(InMemoryConnectorRegistryStore())
    connector = _MinimalConnector()
    descriptor = register_connector(
        registry, connector, connector_id="demo-1", name="Demo", version="1.0", publisher="TMIS",
        config_schema={"api_key": "string"},
    )
    assert descriptor.connector_type is ConnectorType.CRM
    assert registry.get_implementation("demo-1") is connector
    assert descriptor.config_schema == {"api_key": "string"}


@pytest.mark.asyncio
async def test_in_memory_fake_connector_read_write() -> None:
    fake = InMemoryFakeConnector(records=[ConnectorRecord(external_id="e1", data={})])
    assert await fake.authenticate({}) is True
    records = await fake.read({})
    assert len(records) == 1
    result = await fake.write({}, ConnectorRecord(external_id="e2", data={"x": "1"}))
    assert result.success is True
    assert len(fake.written) == 1


@pytest.mark.asyncio
async def test_in_memory_fake_connector_fail_auth() -> None:
    fake = InMemoryFakeConnector(fail_auth=True)
    assert await fake.authenticate({}) is False


@pytest.mark.asyncio
async def test_noop_metrics_recorder_discards() -> None:
    recorder = NoOpMetricsRecorder()
    invoker = ConnectorInvoker(recorder)
    fake = InMemoryFakeConnector(records=[ConnectorRecord(external_id="e1", data={})])
    records = await invoker.safe_read(fake, "c1", "f1", {})
    assert len(records) == 1


@pytest.mark.asyncio
async def test_assert_connector_conforms_rejects_bad_read_return_type() -> None:
    class BadConnector:
        connector_type = ConnectorType.CRM
        capabilities = frozenset({ConnectorCapability.READ})

        async def authenticate(self, config: dict[str, str]) -> bool:
            return True

        async def read(self, config: dict[str, str], since: str | None = None) -> str:
            return "not a list"

    with pytest.raises(ConnectorConformanceError):
        await assert_connector_conforms(BadConnector(), {})  # type: ignore[arg-type]


@pytest.mark.asyncio
@pytest.mark.parametrize("connector_cls", _ALL_DEMO_CONNECTORS)
async def test_reference_connector_conforms_and_reads_seed_data(connector_cls: type) -> None:
    connector = connector_cls()
    await assert_connector_conforms(connector, {})
    records = await connector.read({})
    assert len(records) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("connector_cls", _ALL_DEMO_CONNECTORS)
async def test_reference_connector_write_appends_record(connector_cls: type) -> None:
    connector = connector_cls()
    before = len(await connector.read({}))
    result = await connector.write({}, ConnectorRecord(external_id="new-1", data={"k": "v"}))
    assert result.success is True
    after = await connector.read({})
    assert len(after) == before + 1
