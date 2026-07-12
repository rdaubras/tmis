import pytest

from tmis.integration_hub.connector_framework import (
    ConnectorCapability,
    ConnectorInvoker,
    ConnectorRecord,
    ConnectorType,
    ConnectorWriteResult,
)
from tmis.integration_hub.connector_registry import (
    ConnectorDescriptor,
    ConnectorRegistryEngine,
    ConnectorStatus,
    InMemoryConnectorRegistryStore,
)


class _FakeConnector:
    connector_type = ConnectorType.CRM
    capabilities = frozenset({ConnectorCapability.READ, ConnectorCapability.WRITE})

    def __init__(self, *, fail_read: bool = False) -> None:
        self.fail_read = fail_read

    async def authenticate(self, config: dict[str, str]) -> bool:
        return True

    async def read(
        self, config: dict[str, str], since: str | None = None
    ) -> list[ConnectorRecord]:
        if self.fail_read:
            raise RuntimeError("boom")
        return [ConnectorRecord(external_id="e1", data={"name": "x"})]

    async def write(
        self, config: dict[str, str], record: ConnectorRecord
    ) -> ConnectorWriteResult:
        return ConnectorWriteResult(success=True, external_id=record.external_id)


class _WriteFailingConnector(_FakeConnector):
    async def write(
        self, config: dict[str, str], record: ConnectorRecord
    ) -> ConnectorWriteResult:
        raise RuntimeError("write boom")


class _Metrics:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str, bool]] = []

    def record(
        self,
        connector_id: str,
        firm_id: str,
        operation: str,
        *,
        success: bool,
        duration_ms: float,
        record_count: int = 0,
        error: str | None = None,
    ) -> None:
        self.calls.append((connector_id, firm_id, operation, success))


@pytest.mark.asyncio
async def test_connector_invoker_safe_read_success_records_metric() -> None:
    metrics = _Metrics()
    invoker = ConnectorInvoker(metrics)
    records = await invoker.safe_read(_FakeConnector(), "conn-1", "firm-1", {})
    assert len(records) == 1
    assert metrics.calls == [("conn-1", "firm-1", "read", True)]


@pytest.mark.asyncio
async def test_connector_invoker_safe_read_failure_records_and_reraises() -> None:
    metrics = _Metrics()
    invoker = ConnectorInvoker(metrics)
    with pytest.raises(RuntimeError):
        await invoker.safe_read(_FakeConnector(fail_read=True), "conn-1", "firm-1", {})
    assert metrics.calls == [("conn-1", "firm-1", "read", False)]


@pytest.mark.asyncio
async def test_connector_invoker_safe_write_success() -> None:
    metrics = _Metrics()
    invoker = ConnectorInvoker(metrics)
    result = await invoker.safe_write(
        _FakeConnector(), "conn-1", "firm-1", {}, ConnectorRecord(external_id="e1", data={})
    )
    assert result.success is True
    assert metrics.calls == [("conn-1", "firm-1", "write", True)]


@pytest.mark.asyncio
async def test_connector_invoker_safe_write_failure_never_raises() -> None:
    metrics = _Metrics()
    invoker = ConnectorInvoker(metrics)
    result = await invoker.safe_write(
        _WriteFailingConnector(),
        "conn-1",
        "firm-1",
        {},
        ConnectorRecord(external_id="e1", data={}),
    )
    assert result.success is False
    assert "write boom" in result.detail
    assert metrics.calls == [("conn-1", "firm-1", "write", False)]


def test_connector_registry_register_get_list() -> None:
    registry = ConnectorRegistryEngine(InMemoryConnectorRegistryStore())
    implementation = _FakeConnector()
    descriptor = ConnectorDescriptor(
        id="conn-1",
        name="Fake",
        version="1.0",
        publisher="TMIS",
        connector_type=ConnectorType.CRM,
        capabilities=frozenset({ConnectorCapability.READ}),
    )
    registry.register(descriptor, implementation)

    assert registry.get_descriptor("conn-1") is descriptor
    assert registry.get_implementation("conn-1") is implementation
    assert registry.list_connectors() == [descriptor]
    assert registry.list_connectors(connector_type=ConnectorType.CRM) == [descriptor]
    assert registry.list_connectors(connector_type=ConnectorType.BILLING) == []


def test_connector_registry_enable_disable() -> None:
    registry = ConnectorRegistryEngine(InMemoryConnectorRegistryStore())
    descriptor = ConnectorDescriptor(
        id="conn-1",
        name="Fake",
        version="1.0",
        publisher="TMIS",
        connector_type=ConnectorType.CRM,
        capabilities=frozenset({ConnectorCapability.READ}),
    )
    registry.register(descriptor, _FakeConnector())

    registry.disable("conn-1")
    assert registry.get_descriptor("conn-1").status is ConnectorStatus.DISABLED
    assert registry.list_connectors(status=ConnectorStatus.ACTIVE) == []

    registry.enable("conn-1")
    assert registry.get_descriptor("conn-1").status is ConnectorStatus.ACTIVE


def test_connector_registry_unknown_id_raises_keyerror() -> None:
    registry = ConnectorRegistryEngine(InMemoryConnectorRegistryStore())
    with pytest.raises(KeyError):
        registry.get_descriptor("missing")
    with pytest.raises(KeyError):
        registry.get_implementation("missing")
