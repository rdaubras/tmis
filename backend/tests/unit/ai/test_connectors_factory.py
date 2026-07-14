import pytest

from tmis.ai.connectors import factory
from tmis.ai.connectors.adapters.http_connector import HttpConnector
from tmis.ai.connectors.adapters.judilibre_connector import JudilibreConnector
from tmis.ai.connectors.adapters.legifrance_connector import LegifranceConnector
from tmis.ai.connectors.codes_connector import CodesConnector
from tmis.ai.connectors.doctrine_connector import DoctrineConnector
from tmis.ai.connectors.jurisprudence_connector import JurisprudenceConnector
from tmis.core.config import Settings


def test_build_codes_connector_falls_back_to_fixture_with_no_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(factory, "get_settings", lambda: Settings())

    connector = factory.build_codes_connector()

    assert isinstance(connector, CodesConnector)


def test_build_codes_connector_uses_legifrance_when_piste_is_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        factory,
        "get_settings",
        lambda: Settings(piste_client_id="id", piste_client_secret="secret"),
    )

    connector = factory.build_codes_connector()

    assert isinstance(connector, LegifranceConnector)


def test_build_jurisprudence_connector_falls_back_to_fixture_with_no_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(factory, "get_settings", lambda: Settings())

    connector = factory.build_jurisprudence_connector()

    assert isinstance(connector, JurisprudenceConnector)


def test_build_jurisprudence_connector_uses_judilibre_when_piste_is_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        factory,
        "get_settings",
        lambda: Settings(piste_client_id="id", piste_client_secret="secret"),
    )

    connector = factory.build_jurisprudence_connector()

    assert isinstance(connector, JudilibreConnector)


def test_build_doctrine_connector_falls_back_to_fixture_with_no_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(factory, "get_settings", lambda: Settings())

    connector = factory.build_doctrine_connector()

    assert isinstance(connector, DoctrineConnector)


def test_build_doctrine_connector_uses_http_connector_when_base_url_is_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        factory,
        "get_settings",
        lambda: Settings(doctrine_connector_base_url="https://doctrine.example.test"),
    )

    connector = factory.build_doctrine_connector()

    assert isinstance(connector, HttpConnector)
    assert connector.connector_name == "doctrine"


def test_codes_connector_status_reports_the_missing_env_vars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(factory, "get_settings", lambda: Settings())

    configured, detail = factory.codes_connector_status()

    assert configured is False
    assert "PISTE" in detail
