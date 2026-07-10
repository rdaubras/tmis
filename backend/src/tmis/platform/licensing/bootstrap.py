from functools import lru_cache

from tmis.core.config import get_settings
from tmis.platform.licensing.engine import LicenseEngine
from tmis.platform.licensing.signing import LicenseKeySigner
from tmis.platform.licensing.store import InMemoryLicenseStore


@lru_cache
def get_license_engine() -> LicenseEngine:
    """Process-wide `LicenseEngine` singleton — see
    docs/47-guide-securite-entreprise.md."""
    settings = get_settings()
    return LicenseEngine(InMemoryLicenseStore(), LicenseKeySigner(settings.license_signing_key))
