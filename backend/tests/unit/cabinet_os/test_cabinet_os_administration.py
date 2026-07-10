import pytest

from tmis.cabinet_os.administration.engine import AdministrationEngine
from tmis.cabinet_os.administration.monitoring import StaticMonitoringAdapter
from tmis.cabinet_os.administration.schemas import FirmStatus
from tmis.cabinet_os.administration.store import (
    InMemoryConnectorRegistry,
    InMemoryFirmRegistry,
    InMemoryGlobalConfig,
)


def _engine() -> AdministrationEngine:
    return AdministrationEngine(
        InMemoryFirmRegistry(),
        InMemoryConnectorRegistry(),
        InMemoryGlobalConfig(),
        StaticMonitoringAdapter(),
    )


def test_register_firm_starts_in_trial() -> None:
    engine = _engine()
    firm = engine.register_firm("Cabinet Durand")

    assert firm.status is FirmStatus.TRIAL
    assert firm in engine.list_firms()


def test_set_firm_status_suspends_a_firm() -> None:
    engine = _engine()
    firm = engine.register_firm("Cabinet Durand")

    suspended = engine.set_firm_status(firm.id, FirmStatus.SUSPENDED)

    assert suspended.status is FirmStatus.SUSPENDED


def test_set_firm_status_unknown_firm_raises() -> None:
    engine = _engine()
    with pytest.raises(ValueError, match="Unknown firm"):
        engine.set_firm_status("nope", FirmStatus.ACTIVE)


def test_register_and_list_connectors() -> None:
    engine = _engine()
    engine.register_connector("legifrance", "legal_research")

    connectors = engine.list_connectors()

    assert len(connectors) == 1
    assert connectors[0].enabled is True


def test_disable_a_connector() -> None:
    engine = _engine()
    engine.register_connector("legifrance", "legal_research")

    disabled = engine.set_connector_enabled("legifrance", False)

    assert disabled.enabled is False


def test_disable_unknown_connector_raises() -> None:
    engine = _engine()
    with pytest.raises(ValueError, match="Unknown connector"):
        engine.set_connector_enabled("nope", False)


def test_global_config_set_and_get() -> None:
    engine = _engine()
    engine.set_global_config("maintenance_mode", "false")

    assert engine.get_global_config("maintenance_mode") == "false"


def test_global_config_get_returns_default_when_unset() -> None:
    engine = _engine()
    assert engine.get_global_config("unknown_key", default="fallback") == "fallback"


def test_monitoring_snapshot_is_a_stub() -> None:
    engine = _engine()
    snapshot = engine.monitoring_snapshot()

    assert snapshot.cpu_percent == 0.0
    assert snapshot.computed_at is not None
