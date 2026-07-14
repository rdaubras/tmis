import pytest

from tmis.ai.connectors.adapters.http_connector import HttpConnector
from tmis.core.config import Settings
from tmis.legal_research.connectors import factory
from tmis.legal_research.connectors.internal_documentation_connector import (
    InternalDocumentationConnector,
)
from tmis.legal_research.connectors.private_database_connector import PrivateDatabaseConnector


def test_build_internal_documentation_connector_falls_back_to_fixture_with_no_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(factory, "get_settings", lambda: Settings())

    connector = factory.build_internal_documentation_connector()

    assert isinstance(connector, InternalDocumentationConnector)


def test_build_internal_documentation_connector_uses_http_connector_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        factory,
        "get_settings",
        lambda: Settings(
            internal_documentation_connector_base_url="https://cabinet.example.test"
        ),
    )

    connector = factory.build_internal_documentation_connector()

    assert isinstance(connector, HttpConnector)
    assert connector.connector_name == "internal_documentation"


def test_build_private_database_connector_falls_back_to_fixture_with_no_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(factory, "get_settings", lambda: Settings())

    connector = factory.build_private_database_connector()

    assert isinstance(connector, PrivateDatabaseConnector)


def test_build_private_database_connector_uses_http_connector_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        factory,
        "get_settings",
        lambda: Settings(private_database_connector_base_url="https://provider.example.test"),
    )

    connector = factory.build_private_database_connector()

    assert isinstance(connector, HttpConnector)
    assert connector.connector_name == "private_database"
