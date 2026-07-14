from tmis.ai.connectors.adapters.http_client_factory import get_connector_http_client
from tmis.ai.connectors.adapters.http_connector import HttpConnector
from tmis.ai.connectors.ports import ConnectorPort
from tmis.core.config import get_settings
from tmis.core.logging import get_logger
from tmis.legal_research.connectors.internal_documentation_connector import (
    InternalDocumentationConnector,
)
from tmis.legal_research.connectors.private_database_connector import PrivateDatabaseConnector

logger = get_logger(__name__)


def internal_documentation_connector_status() -> tuple[bool, str]:
    settings = get_settings()
    if settings.internal_documentation_connector_base_url:
        return True, (
            f"using the configured HTTP source at "
            f"{settings.internal_documentation_connector_base_url}"
        )
    return False, (
        "TMIS_INTERNAL_DOCUMENTATION_CONNECTOR_BASE_URL not configured — "
        "using the in-memory fixture connector"
    )


def private_database_connector_status() -> tuple[bool, str]:
    settings = get_settings()
    if settings.private_database_connector_base_url:
        return True, (
            f"using the configured HTTP source at {settings.private_database_connector_base_url}"
        )
    return False, (
        "TMIS_PRIVATE_DATABASE_CONNECTOR_BASE_URL not configured — "
        "using the in-memory fixture connector"
    )


def build_internal_documentation_connector() -> ConnectorPort:
    """Real adapter if a firm-specific HTTP source is configured,
    otherwise the Sprint 5 in-memory fixture (see
    docs/154-guide-configuration-connecteurs.md)."""
    configured, detail = internal_documentation_connector_status()
    if not configured:
        logger.warning(
            "connector.fixture_fallback", connector="internal_documentation", reason=detail
        )
        return InternalDocumentationConnector()
    settings = get_settings()
    assert settings.internal_documentation_connector_base_url  # noqa: S101 — guarded above
    return HttpConnector(
        get_connector_http_client(),
        connector_name="internal_documentation",
        base_url=settings.internal_documentation_connector_base_url,
        api_key=settings.internal_documentation_connector_api_key,
    )


def build_private_database_connector() -> ConnectorPort:
    configured, detail = private_database_connector_status()
    if not configured:
        logger.warning("connector.fixture_fallback", connector="private_database", reason=detail)
        return PrivateDatabaseConnector()
    settings = get_settings()
    assert settings.private_database_connector_base_url  # noqa: S101 — guarded above
    return HttpConnector(
        get_connector_http_client(),
        connector_name="private_database",
        base_url=settings.private_database_connector_base_url,
        api_key=settings.private_database_connector_api_key,
    )
