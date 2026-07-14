from tmis.ai.connectors.adapters.http_client_factory import get_connector_http_client
from tmis.ai.connectors.adapters.http_connector import HttpConnector
from tmis.ai.connectors.adapters.judilibre_connector import JudilibreConnector
from tmis.ai.connectors.adapters.legifrance_connector import LegifranceConnector
from tmis.ai.connectors.adapters.piste_oauth import PisteOAuthTokenProvider
from tmis.ai.connectors.codes_connector import CodesConnector
from tmis.ai.connectors.doctrine_connector import DoctrineConnector
from tmis.ai.connectors.jurisprudence_connector import JurisprudenceConnector
from tmis.ai.connectors.ports import ConnectorPort
from tmis.core.config import get_settings
from tmis.core.logging import get_logger

logger = get_logger(__name__)


def _piste_configured() -> bool:
    settings = get_settings()
    return bool(settings.piste_client_id and settings.piste_client_secret)


def _piste_token_provider() -> PisteOAuthTokenProvider:
    settings = get_settings()
    assert settings.piste_client_id and settings.piste_client_secret  # noqa: S101 — guarded by _piste_configured() at every call site
    return PisteOAuthTokenProvider(
        get_connector_http_client(),
        token_url=settings.piste_oauth_token_url,
        client_id=settings.piste_client_id,
        client_secret=settings.piste_client_secret,
    )


def codes_connector_status() -> tuple[bool, str]:
    if _piste_configured():
        return True, "PISTE credentials configured — using the real Légifrance API"
    return False, (
        "TMIS_PISTE_CLIENT_ID/TMIS_PISTE_CLIENT_SECRET not configured — "
        "using the in-memory fixture connector"
    )


def jurisprudence_connector_status() -> tuple[bool, str]:
    if _piste_configured():
        return True, "PISTE credentials configured — using the real Judilibre API"
    return False, (
        "TMIS_PISTE_CLIENT_ID/TMIS_PISTE_CLIENT_SECRET not configured — "
        "using the in-memory fixture connector"
    )


def doctrine_connector_status() -> tuple[bool, str]:
    settings = get_settings()
    if settings.doctrine_connector_base_url:
        return True, f"using the configured HTTP source at {settings.doctrine_connector_base_url}"
    return False, (
        "TMIS_DOCTRINE_CONNECTOR_BASE_URL not configured — using the in-memory fixture connector"
    )


def build_codes_connector() -> ConnectorPort:
    """Real adapter if PISTE credentials are configured, otherwise the
    Sprint 2 in-memory fixture — see `codes_connector_status()` for what
    decides this and `docs/154-guide-configuration-connecteurs.md` for how
    to configure the real backend."""
    configured, detail = codes_connector_status()
    if not configured:
        logger.warning("connector.fixture_fallback", connector="codes", reason=detail)
        return CodesConnector()
    settings = get_settings()
    return LegifranceConnector(
        get_connector_http_client(),
        _piste_token_provider(),
        base_url=settings.legifrance_api_base_url,
    )


def build_jurisprudence_connector() -> ConnectorPort:
    configured, detail = jurisprudence_connector_status()
    if not configured:
        logger.warning("connector.fixture_fallback", connector="jurisprudence", reason=detail)
        return JurisprudenceConnector()
    settings = get_settings()
    return JudilibreConnector(
        get_connector_http_client(),
        _piste_token_provider(),
        base_url=settings.judilibre_api_base_url,
    )


def build_doctrine_connector() -> ConnectorPort:
    configured, detail = doctrine_connector_status()
    if not configured:
        logger.warning("connector.fixture_fallback", connector="doctrine", reason=detail)
        return DoctrineConnector()
    settings = get_settings()
    assert settings.doctrine_connector_base_url  # noqa: S101 — guarded by doctrine_connector_status() above
    return HttpConnector(
        get_connector_http_client(),
        connector_name="doctrine",
        base_url=settings.doctrine_connector_base_url,
        api_key=settings.doctrine_connector_api_key,
    )
