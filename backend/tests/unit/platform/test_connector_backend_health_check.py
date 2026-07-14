import pytest

from tmis.platform.health import connector_backend_check
from tmis.platform.health.connector_backend_check import ConnectorBackendHealthCheck
from tmis.platform.health.schemas import HealthStatus


def test_reports_up_when_every_connector_is_on_its_real_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(connector_backend_check, "codes_connector_status", lambda: (True, "ok"))
    monkeypatch.setattr(
        connector_backend_check, "jurisprudence_connector_status", lambda: (True, "ok")
    )
    monkeypatch.setattr(connector_backend_check, "doctrine_connector_status", lambda: (True, "ok"))
    monkeypatch.setattr(
        connector_backend_check, "internal_documentation_connector_status", lambda: (True, "ok")
    )
    monkeypatch.setattr(
        connector_backend_check, "private_database_connector_status", lambda: (True, "ok")
    )

    result = ConnectorBackendHealthCheck().check()

    assert result.status == HealthStatus.UP
    assert result.detail == ""


def test_reports_degraded_and_names_connectors_still_on_fixture_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(connector_backend_check, "codes_connector_status", lambda: (True, "ok"))
    monkeypatch.setattr(
        connector_backend_check,
        "jurisprudence_connector_status",
        lambda: (False, "no PISTE credentials"),
    )
    monkeypatch.setattr(connector_backend_check, "doctrine_connector_status", lambda: (True, "ok"))
    monkeypatch.setattr(
        connector_backend_check,
        "internal_documentation_connector_status",
        lambda: (False, "no base url"),
    )
    monkeypatch.setattr(
        connector_backend_check, "private_database_connector_status", lambda: (True, "ok")
    )

    result = ConnectorBackendHealthCheck().check()

    assert result.status == HealthStatus.DEGRADED
    assert "jurisprudence: no PISTE credentials" in result.detail
    assert "internal_documentation: no base url" in result.detail
    assert "codes" not in result.detail
